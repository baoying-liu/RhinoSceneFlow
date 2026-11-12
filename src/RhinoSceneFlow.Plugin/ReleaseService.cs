using System.Diagnostics;
using System.Net.Http;
using System.Security.Cryptography;
using System.Text.Json;
using Rhino;
using RhinoSceneFlow.Core;

namespace RhinoSceneFlow.Plugin;

internal static class ReleaseService
{
    private static readonly CancellationTokenSource stopping = new();
    private static readonly SemaphoreSlim gate = new(1);
    internal static ReleaseOffer? Offer { get; private set; }
    internal static string Status { get; private set; } = "not_checked";
    internal static string? Download { get; private set; }
    internal static bool Busy { get; private set; }
    internal static bool AutoCheck
    {
        get { try { using var json = JsonDocument.Parse(File.ReadAllText(Path.Combine(InstallationContext.ReleaseData, "options.json"))); return json.RootElement.GetProperty("autoCheck").GetBoolean(); } catch (Exception e) when (e is IOException or JsonException or UnauthorizedAccessException or KeyNotFoundException or InvalidOperationException) { return true; } }
        set { Directory.CreateDirectory(InstallationContext.ReleaseData); File.WriteAllText(Path.Combine(InstallationContext.ReleaseData, "options.json"), JsonSerializer.Serialize(new { autoCheck = value })); }
    }
    internal static void Start() => RhinoApp.Idle += OnIdle;
    private static void OnIdle(object? sender, EventArgs args)
    {
        RhinoApp.Idle -= OnIdle;
        _ = ConnectionService.CheckAsync();
        if (InstallationContext.Sandbox) return;
        if (InstallationContext.Managed)
        {
            try
            {
                var version = typeof(ReleaseService).Assembly.GetName().Version!.ToString(3);
                var acknowledged = Path.Combine(InstallationContext.ReleaseData, "acknowledged-version.txt");
                if (!File.Exists(acknowledged) || File.ReadAllText(acknowledged) != version)
                {
                    bool en = PluginPreferences.Load().ResolvedLanguage == "en";
                    Eto.Forms.MessageBox.Show(en ? $"SceneFlow {version} is installed and loaded. Your libraries and boards have been retained." : $"SceneFlow {version} 已安装并加载。素材库和画板已保留。", "SceneFlow");
                    Directory.CreateDirectory(InstallationContext.ReleaseData); File.WriteAllText(acknowledged, version);
                }
            }
            catch (Exception e) when (e is IOException or UnauthorizedAccessException) { RhinoApp.WriteLine("SceneFlow: installation receipt could not be saved."); }
        }
        if (AutoCheck) _ = CheckAsync();
    }
    internal static async Task CheckAsync()
    {
        if (!await gate.WaitAsync(0)) return;
        Busy = true; Status = "checking";
        try
        {
            Offer = await ReleaseFeed.CheckAsync(typeof(ReleaseService).Assembly.GetName().Version!, stopping.Token);
            Status = Offer is null ? "current" : "available";
            if (Offer is not null) RhinoApp.InvokeOnUiThread((Action)(() => RhinoApp.WriteLine(PluginPreferences.Load().ResolvedLanguage == "en" ? "SceneFlow update available. Open Settings > Connections and updates." : "SceneFlow 有新版，请在设置的连接与更新中查看。")));
        }
        catch (OperationCanceledException) { Status = stopping.IsCancellationRequested ? "cancelled" : "offline"; }
        catch (InvalidOperationException e) { Status = e.Message == "release_not_public" ? "not_public" : e.Message == "release_rate_limit" ? "rate_limit" : "failed"; }
        catch (Exception e) when (e is HttpRequestException or JsonException or InvalidDataException) { Status = "offline"; }
        finally { Busy = false; gate.Release(); }
    }
    internal static async Task DownloadAsync()
    {
        if (InstallationContext.Sandbox || !InstallationContext.Managed) throw new InvalidOperationException("production_only");
        if (string.IsNullOrWhiteSpace(InstallationContext.PublisherThumbprint)) throw new InvalidOperationException("signing_not_configured");
        if (!await gate.WaitAsync(0)) return;
        Busy = true;
        string? temporary = null;
        try
        {
            var offer = Offer ?? throw new InvalidOperationException("check_first");
            if (offer.Installer is null || offer.Sha256 is null) throw new InvalidOperationException("installer_not_published");
            Status = "downloading";
            string directory = Path.Combine(InstallationContext.ReleaseData, "downloads", offer.Version);
            Directory.CreateDirectory(directory);
            temporary = Path.Combine(directory, Guid.NewGuid().ToString("N") + ".partial");
            using var http = new HttpClient { Timeout = TimeSpan.FromMinutes(15) };
            using var response = await http.GetAsync(offer.Installer, HttpCompletionOption.ResponseHeadersRead, stopping.Token);
            response.EnsureSuccessStatusCode();
            await using (var source = await response.Content.ReadAsStreamAsync(stopping.Token))
            await using (var destination = File.Create(temporary))
            {
                byte[] buffer = new byte[128 * 1024]; long total = 0; int count;
                while ((count = await source.ReadAsync(buffer, stopping.Token)) > 0)
                {
                    total += count; if (total > offer.Bytes) throw new InvalidDataException("Unexpected download length.");
                    await destination.WriteAsync(buffer.AsMemory(0, count), stopping.Token);
                }
                if (total != offer.Bytes) throw new InvalidDataException("Incomplete download.");
            }
            using (var stream = File.OpenRead(temporary))
                if (!Convert.ToHexString(SHA256.HashData(stream)).Equals(offer.Sha256, StringComparison.OrdinalIgnoreCase)) throw new InvalidDataException("Installer hash mismatch.");
            var final = Path.Combine(directory, $"SceneFlow-Setup-{offer.Version}-win-x64.exe");
            string publisher = InstallationContext.PublisherThumbprint;
            await Task.Run(() => SignedInstaller.Verify(temporary, publisher), stopping.Token);
            File.Move(temporary, final, true); Download = final; Status = "ready";
        }
        catch { Status = "download_failed"; throw; }
        finally { if (temporary is not null && File.Exists(temporary)) File.Delete(temporary); Busy = false; gate.Release(); }
    }
    internal static async Task InstallAfterExitAsync()
    {
        if (!InstallationContext.Managed || InstallationContext.Sandbox) throw new InvalidOperationException("production_only");
        if (!await gate.WaitAsync(0)) return;
        Busy = true;
        try
        {
        void RequireIdle()
        {
            if (MaterialGeneration.HasActiveWorkers || MaterialChat.Busy || RandomTextureService.Busy || SeasonalGeneration.Busy || ConnectionService.Busy)
                throw new InvalidOperationException(PluginPreferences.Load().ResolvedLanguage == "en" ? "Finish or cancel active SceneFlow tasks before updating." : "请先完成或取消 SceneFlow 正在运行的任务。");
        }
        RequireIdle();
        string file = Download ?? throw new InvalidOperationException("download_first");
        var offer = Offer ?? throw new InvalidOperationException("check_first");
        string publisher = InstallationContext.PublisherThumbprint;
        await Task.Run(() => SignedInstaller.Verify(file, publisher), stopping.Token);
        // Run from a private snapshot: an installed updater must not lock files that MSI replaces.
        string runner = Path.Combine(InstallationContext.ReleaseData, "runners", Guid.NewGuid().ToString("N"));
        string runnerBin = Path.Combine(runner, "Updater");
        await Task.Run(() =>
        {
            Directory.CreateDirectory(runnerBin);
            string source = Path.Combine(InstallationContext.DirectoryPath, "Updater");
            foreach (string input in Directory.EnumerateFiles(source, "*", SearchOption.AllDirectories))
            {
                string target = Path.Combine(runnerBin, Path.GetRelativePath(source, input));
                Directory.CreateDirectory(Path.GetDirectoryName(target)!); File.Copy(input, target);
            }
            File.Copy(Path.Combine(InstallationContext.DirectoryPath, "installation.json"), Path.Combine(runner, "installation.json"));
        });
        // Recheck after every slow preparatory operation, before closing any service/host.
        RequireIdle();
        await PostProduction.ShutdownForUpdateAsync();
        RequireIdle();
        var info = new ProcessStartInfo(Path.Combine(runnerBin, "SceneFlow.Update.exe")) { UseShellExecute = false, CreateNoWindow = true };
        string cancelFlag = Path.Combine(runner, "cancelled");
        foreach (var arg in new[] { "--wait-install", file, offer.Sha256!, InstallationContext.PublisherThumbprint, Environment.ProcessId.ToString(), Process.GetCurrentProcess().StartTime.ToUniversalTime().Ticks.ToString(), cancelFlag }) info.ArgumentList.Add(arg);
        using var child = Process.Start(info) ?? throw new IOException("Updater did not start.");
        // Rhino owns Save/Discard/Cancel; cancellation never leads to a forced exit.
        RhinoApp.RunScript("_Exit", false);
        if (!stopping.IsCancellationRequested) File.WriteAllText(cancelFlag, "Rhino exit cancelled.");
        }
        finally { Busy = false; gate.Release(); }
    }
    internal static object State() => new { version = typeof(ReleaseService).Assembly.GetName().Version!.ToString(3), sandbox = InstallationContext.Sandbox, managed = InstallationContext.Managed, autoCheck = AutoCheck, status = Status, busy = Busy, offer = Offer, downloaded = Download is not null, signedUpdatesConfigured = InstallationContext.PublisherThumbprint.Length > 0, runtime = InstallationContext.Python, studioData = InstallationContext.StudioData };
    internal static void Stop() { RhinoApp.Idle -= OnIdle; stopping.Cancel(); }
}

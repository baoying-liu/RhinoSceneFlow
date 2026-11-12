using System.Diagnostics;
using System.Text.RegularExpressions;
using Microsoft.Win32;
using Rhino.PlugIns;
using RhinoSceneFlow.Core;

namespace RhinoSceneFlow.Plugin;

internal static class ConnectionService
{
    internal static string Auth { get; private set; } = "not_checked";
    internal static string DeviceCode { get; private set; } = "";
    internal static string Runtime { get; private set; } = "not_checked";
    internal static bool Busy { get; private set; }
    internal static bool Checked { get; private set; }
    internal static long Revision { get; private set; }
    internal static bool AiReady => Checked && !Busy && Runtime == "ready" && Auth == "chatgpt";
    internal static bool ChatReady => AiReady && WebViewInstalled();
    private static CancellationTokenSource? login;
    internal static object Inspect()
    {
        return new { sandbox = InstallationContext.Sandbox, managed = InstallationContext.Managed,
            platformLoaded = PlugIn.Find(new Guid("2668d7ed-f507-4a68-8295-8172147a0e39")) is not null,
            codexInstalled = CodexImageRunner.FindExecutable() is not null, auth = Auth, busy = Busy, deviceCode = DeviceCode,
            runtimeInstalled = File.Exists(InstallationContext.Python), runtime = Runtime, webViewInstalled = WebViewInstalled(),
            verified = AiReady, checkedOnce = Checked, revision = Revision, imageAccess = "not_tested" };
    }
    private static bool WebViewInstalled()
    {
        // Rhino may preload a different WebView2 SDK. Optional environment detection must
        // not bind to an SDK method signature (or mistake Edge Beta for production Runtime).
        const string key = @"Software\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}";
        foreach (var hive in new[] { RegistryHive.CurrentUser, RegistryHive.LocalMachine })
        foreach (var view in new[] { RegistryView.Registry32, RegistryView.Registry64 })
        {
            try
            {
                using var root = RegistryKey.OpenBaseKey(hive, view);
                using var entry = root.OpenSubKey(key);
                if (Version.TryParse(entry?.GetValue("pv") as string, out var version) && version > new Version(0, 0, 0, 0)) return true;
            }
            catch (Exception e) when (e is UnauthorizedAccessException or System.Security.SecurityException or IOException) { }
        }
        return false;
    }
    internal static async Task CheckAsync()
    {
        if (Busy) return;
        Busy = true;
        Runtime = "checking"; Auth = "checking";
        using var timeout = new CancellationTokenSource(TimeSpan.FromSeconds(15));
        try
        {
            if (!File.Exists(InstallationContext.Python)) Runtime = "missing";
            else
            {
                var probe = await RunAsync(InstallationContext.Python, ["-I", "-X", "utf8", "-c", "import chatkit,fastapi,uvicorn,psd_tools,PIL,numpy,cv2,pyvips"], timeout.Token, false);
                Runtime = probe.Code == 0 ? "ready" : "failed";
            }
            var executable = CodexImageRunner.FindExecutable();
            if (executable is null) { Auth = "missing"; return; }
            var result = await RunAsync(executable, ["login", "status"], timeout.Token, false);
            Auth = result.Code != 0 ? "signed_out" : result.Text.Contains("ChatGPT", StringComparison.OrdinalIgnoreCase) ? "chatgpt" : "api_key";
        }
        catch (OperationCanceledException) { Auth = "timeout"; if (Runtime == "checking") Runtime = "timeout"; }
        catch (Exception e) when (e is IOException or System.ComponentModel.Win32Exception or UnauthorizedAccessException) { Auth = "failed"; if (Runtime == "checking") Runtime = "failed"; }
        finally { Checked = true; Revision++; Busy = false; }
    }
    internal static async Task LoginAsync(bool deviceCode)
    {
        if (Busy) return;
        string executable = CodexImageRunner.FindExecutable() ?? throw new InvalidOperationException("codex_missing");
        Busy = true; DeviceCode = ""; Auth = "signing_in";
        login = new CancellationTokenSource(TimeSpan.FromMinutes(5));
        try
        {
            var result = await RunAsync(executable, deviceCode ? ["login", "--device-auth"] : ["login"], login.Token, deviceCode);
            Auth = result.Code == 0 ? "check_required" : "failed";
        }
        catch (OperationCanceledException) { Auth = "cancelled"; }
        finally { login.Dispose(); login = null; Busy = false; DeviceCode = ""; Revision++; }
        if (Auth == "check_required") await CheckAsync();
    }
    private static async Task<(int Code, string Text)> RunAsync(string executable, string[] arguments, CancellationToken token, bool device)
    {
        var info = new ProcessStartInfo(executable) { UseShellExecute = false, CreateNoWindow = true, RedirectStandardOutput = true, RedirectStandardError = true };
        foreach (string argument in arguments) info.ArgumentList.Add(argument);
        using var process = Process.Start(info) ?? throw new IOException("Codex did not start.");
        using var cancel = token.Register(() => { try { if (!process.HasExited) process.Kill(true); } catch (InvalidOperationException) { } catch (System.ComponentModel.Win32Exception) { } });
        async Task<string> ReadAsync(StreamReader reader)
        {
            var text = new System.Text.StringBuilder(); char[] buffer = new char[512]; int count;
            while ((count = await reader.ReadAsync(buffer, token)) > 0)
            {
                if (text.Length + count > 64 * 1024) throw new IOException("Unexpected Codex login output.");
                text.Append(buffer, 0, count);
                // Only expose the short verification code, never auth URLs, tokens or account files.
                if (device)
                {
                    string clean = Regex.Replace(text.ToString(), @"\x1B\[[0-9;]*[A-Za-z]", "");
                    var match = Regex.Match(clean, @"\b[A-Z0-9]{4}-[A-Z0-9]{4,5}\b");
                    if (match.Success) DeviceCode = match.Value;
                }
            }
            return text.ToString();
        }
        try
        {
            var output = ReadAsync(process.StandardOutput); var error = ReadAsync(process.StandardError);
            await process.WaitForExitAsync(token); return (process.ExitCode, await output + await error);
        }
        finally { try { if (!process.HasExited) process.Kill(true); } catch (InvalidOperationException) { } catch (System.ComponentModel.Win32Exception) { } }
    }
    internal static void CancelLogin() { try { login?.Cancel(); } catch (ObjectDisposedException) { } }
}

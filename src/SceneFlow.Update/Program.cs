using System.Diagnostics;
using System.Security.Cryptography;
using System.Text.Json;
using RhinoSceneFlow.Plugin;

// No privileges, process termination, arbitrary shell text or Rhino document APIs.
if (args.Length != 7 || args[0] != "--wait-install") return;
string data = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "RhinoSceneFlow", "production", "release");
try
{
    string path = Path.GetFullPath(args[1]);
    string allowed = Path.GetFullPath(Path.Combine(data, "downloads")) + Path.DirectorySeparatorChar;
    if (!path.StartsWith(allowed, StringComparison.OrdinalIgnoreCase) || Path.GetExtension(path) != ".exe") throw new InvalidDataException("Invalid installer location.");
    string cancel = Path.GetFullPath(args[6]);
    if (!cancel.Equals(Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "..", "cancelled")), StringComparison.OrdinalIgnoreCase)) throw new InvalidDataException("Invalid cancellation marker.");
    Process? found = null;
    try { found = Process.GetProcessById(int.Parse(args[4])); } catch (ArgumentException) { } // parent can exit before this helper finishes starting
    using var parent = found;
    if (parent is not null && !parent.HasExited && (parent.ProcessName != "Rhino" || parent.StartTime.ToUniversalTime().Ticks != long.Parse(args[5]))) throw new InvalidDataException("Parent identity changed.");
    var deadline = DateTime.UtcNow.AddMinutes(15);
    while (parent is not null && !parent.HasExited)
    {
        if (File.Exists(cancel) || DateTime.UtcNow > deadline) return;
        await Task.Delay(250);
    }
    if (File.Exists(cancel)) return;
    // Bind updates to the currently installed publisher, not merely to a caller-supplied certificate.
    using var receipt = JsonDocument.Parse(File.ReadAllText(Path.Combine(AppContext.BaseDirectory, "..", "installation.json")));
    string publisher = receipt.RootElement.GetProperty("publisherThumbprint").GetString()!;
    if (publisher != args[3]) throw new InvalidDataException("Publisher configuration changed.");
    using (var file = File.OpenRead(path))
        if (!Convert.ToHexString(SHA256.HashData(file)).Equals(args[2], StringComparison.OrdinalIgnoreCase)) throw new InvalidDataException("Installer changed after download.");
    SignedInstaller.Verify(path, publisher);
    using var installer = Process.Start(new ProcessStartInfo(path) { UseShellExecute = true }) ?? throw new IOException("Installer did not start.");
    await installer.WaitForExitAsync();
    Directory.CreateDirectory(data);
    File.WriteAllText(Path.Combine(data, "last-install-attempt.json"), JsonSerializer.Serialize(new { utc = DateTime.UtcNow, exitCode = installer.ExitCode }));
}
catch (Exception e)
{
    Directory.CreateDirectory(data);
    File.WriteAllText(Path.Combine(data, "updater-error.txt"), e.GetType().Name + ": " + e.Message);
}

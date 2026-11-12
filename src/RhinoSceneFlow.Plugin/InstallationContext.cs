using System.Diagnostics;
using System.Text.Json;

namespace RhinoSceneFlow.Plugin;

internal static class InstallationContext
{
    internal static string DirectoryPath => Path.GetDirectoryName(typeof(InstallationContext).Assembly.Location)!;
    internal static bool Sandbox { get; } = DetectSandbox();
    internal static bool Managed => !Sandbox && File.Exists(Path.Combine(DirectoryPath, "installation.json"));
    internal static string ProductData => Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "RhinoSceneFlow");
    // Keep existing development boards intact; a formal install gets its own backend and runtime.
    internal static string StudioData => Path.Combine(ProductData, Managed ? "production/postproduction" : "postproduction");
    internal static string ReleaseData => Path.Combine(ProductData, Sandbox ? "sandbox-release" : "production/release");
    internal static string Python => Managed
        ? Path.Combine(DirectoryPath, "Runtime", "Scripts", "python.exe")
        : Environment.GetEnvironmentVariable("RHINOSCENEFLOW_CHATKIT_PYTHON") ?? Path.Combine(ProductData, "chatkit-runtime", "Scripts", "python.exe");
    private static bool DetectSandbox()
    {
        var path = Path.GetFullPath(typeof(InstallationContext).Assembly.Location);
        if (path.StartsWith(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "RhinoDevSandbox") + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase)) return true;
        try { return Process.GetCurrentProcess().Modules.Cast<ProcessModule>().Any(m => m.ModuleName.Equals("RhinoDevSandbox.Registry64.dll", StringComparison.OrdinalIgnoreCase)); }
        catch (System.ComponentModel.Win32Exception) { return true; } // fail closed: never start production maintenance in an unidentified host
    }
    internal static string PublisherThumbprint
    {
        get
        {
            if (!Managed) return "";
            using var json = JsonDocument.Parse(File.ReadAllText(Path.Combine(DirectoryPath, "installation.json")));
            return json.RootElement.TryGetProperty("publisherThumbprint", out var pin) ? pin.GetString() ?? "" : "";
        }
    }
}

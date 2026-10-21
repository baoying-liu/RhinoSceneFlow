using System.Runtime.InteropServices;
using Rhino.PlugIns;

[assembly: Guid("8b902013-73dd-4227-b45b-896f6a33f134")]

namespace RhinoSceneFlow.Plugin;

public sealed class SceneFlowPlugin : PlugIn
{
    public static SceneFlowPlugin Instance { get; private set; } = null!;
    public SceneFlowPlugin() => Instance = this;

    public string ExportDirectory
    {
        get => Settings.GetString("ExportDirectory", Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments), "RhinoSceneFlow", "Exports"));
        set { Settings.SetString("ExportDirectory", value); SaveSettings(); }
    }
}

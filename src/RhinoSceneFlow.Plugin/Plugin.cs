using System.Runtime.InteropServices;
using Rhino.PlugIns;

[assembly: Guid("8b902013-73dd-4227-b45b-896f6a33f134")]

namespace RhinoSceneFlow.Plugin;

public sealed class SceneFlowPlugin : PlugIn
{
    public static SceneFlowPlugin Instance { get; private set; } = null!;
    public SceneFlowPlugin() => Instance = this;

    public string MaterialDirectory
    {
        get=>Settings.GetString("MaterialDirectory",Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments),"RhinoSceneFlow","Materials"));
        set{if(!Path.IsPathFullyQualified(value))throw new ArgumentException("材质库需要绝对路径。");Settings.SetString("MaterialDirectory",Path.GetFullPath(value));SaveSettings();}
    }

    public string ExportDirectory
    {
        get => Settings.GetString("ExportDirectory", Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments), "RhinoSceneFlow", "Exports"));
        set { Settings.SetString("ExportDirectory", value); SaveSettings(); }
    }
}

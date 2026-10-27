using System.Runtime.InteropServices;
using Rhino.PlugIns;

[assembly: Guid("8b902013-73dd-4227-b45b-896f6a33f134")]

namespace RhinoSceneFlow.Plugin;

public sealed class SceneFlowPlugin : PlugIn
{
    public static SceneFlowPlugin Instance { get; private set; } = null!;
    public SceneFlowPlugin() => Instance = this;
    protected override void OnShutdown(){MaterialChat.StopAll();UnwrapService.StopAll();MaterialGeneration.StopAll();base.OnShutdown();}

    public string MaterialDirectory
    {
        get=>Settings.GetString("MaterialDirectory",Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments),"RhinoSceneFlow","Materials"));
        set{if(MaterialGeneration.HasActiveWorkers||MaterialChat.Busy)throw new InvalidOperationException("图片生成期间不能切换材质库，请先完成或取消任务。");if(!Path.IsPathFullyQualified(value))throw new ArgumentException("材质库需要绝对路径。");Settings.SetString("MaterialDirectory",Path.GetFullPath(value));SaveSettings();}
    }

    public string ExportDirectory
    {
        get => Settings.GetString("ExportDirectory", Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments), "RhinoSceneFlow", "Exports"));
        set { Settings.SetString("ExportDirectory", value); SaveSettings(); }
    }
}

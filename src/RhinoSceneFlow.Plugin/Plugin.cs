using System.Runtime.InteropServices;
using Rhino.PlugIns;

[assembly: Guid("8b902013-73dd-4227-b45b-896f6a33f134")]

namespace RhinoSceneFlow.Plugin;

public sealed class SceneFlowPlugin : PlugIn
{
    public static SceneFlowPlugin Instance { get; private set; } = null!;
    public SceneFlowPlugin() => Instance = this;
    protected override LoadReturnCode OnLoad(ref string errorMessage){try{UiPresentation.Start();UvRenderProvider.Start(this);PlantService.Start();SceneFlowWorkspace.Register(this);SceneFlowToolbar.RegisterWhenIdle();return LoadReturnCode.Success;}catch(Exception e){errorMessage=e.Message;return LoadReturnCode.ErrorShowDialog;}}
    protected override void OnShutdown(){SeasonalGeneration.Stop();SceneFlowWorkspace.Stop();UiPresentation.Stop();PlantService.Stop();RandomTextureService.Stop();CatalogService.Stop();UvRenderProvider.Stop();MaterialChat.StopAll();UnwrapService.StopAll();MaterialGeneration.StopAll();base.OnShutdown();}

    public string MaterialDirectory
    {
        get=>Settings.GetString("MaterialDirectory",Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments),"RhinoSceneFlow","Materials"));
        set{if(SeasonalGeneration.Busy||MaterialGeneration.HasActiveWorkers||MaterialChat.Busy||CatalogService.Busy||RandomTextureService.Busy)throw new InvalidOperationException("材质任务期间不能切换材质库，请先完成或取消任务。");if(!Path.IsPathFullyQualified(value))throw new ArgumentException("材质库需要绝对路径。");Settings.SetString("MaterialDirectory",Path.GetFullPath(value));SaveSettings();}
    }

    public string ExportDirectory
    {
        get => Settings.GetString("ExportDirectory", Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments), "RhinoSceneFlow", "Exports"));
        set { Settings.SetString("ExportDirectory", value); SaveSettings(); }
    }
}

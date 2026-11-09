using Rhino;
using Rhino.Commands;
using Rhino.UI;

namespace RhinoSceneFlow.Plugin;

internal static class SceneFlowToolbar
{
    internal static void RegisterWhenIdle() => RhinoApp.Idle += Register;
    private static void Register(object? sender,EventArgs e)
    {
        RhinoApp.Idle-=Register;
        try{Open(false);}catch(Exception error){RhinoApp.WriteLine("SceneFlow toolbar: "+error.Message);}
    }
    internal static ToolbarFile Open(bool show)
    {
        var existing=RhinoApp.ToolbarFiles.FindByName("RhinoSceneFlow",true);
        if(existing is null)
        {
            // Keep customizations outside immutable snapshots and Rhino's formal
            // profile. Sandbox and normal installs must not share a writable RUI.
            string local=Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            string assembly=typeof(SceneFlowToolbar).Assembly.Location;
            bool sandbox=Path.GetFullPath(assembly).StartsWith(Path.Combine(local,"RhinoDevSandbox","deployments")+Path.DirectorySeparatorChar,StringComparison.OrdinalIgnoreCase);
            string folder=Path.Combine(local,"RhinoSceneFlow","Toolbars",sandbox?"Sandbox":"User");
            Directory.CreateDirectory(folder);string path=Path.Combine(folder,"RhinoSceneFlow.rui");
            if(!File.Exists(path))File.Copy(Path.Combine(Path.GetDirectoryName(typeof(SceneFlowToolbar).Assembly.Location)!,"RhinoSceneFlow.rui"),path);
            existing=RhinoApp.ToolbarFiles.FindByPath(path)??RhinoApp.ToolbarFiles.Open(path);
        }
        if(existing is null)throw new InvalidOperationException("Cannot load SceneFlow toolbar.");
        if(show)
        {
            if(existing.GroupCount>0)for(int i=0;i<existing.GroupCount;i++)existing.GetGroup(i).Visible=true;
            // Rhino 8 containers are not exposed by the legacy GroupCount API.
            else if(!RhinoApp.RunScript("_-ShowToolbar SceneFlow _Enter",false))throw new InvalidOperationException("Cannot show SceneFlow toolbar.");
        }
        return existing;
    }
}

[CommandStyle(Style.ScriptRunner)]
public sealed class SceneFlowToolbarCommand:Command
{
    public override string EnglishName=>"RhinoSceneFlowToolbar";
    protected override Result RunCommand(RhinoDoc doc,RunMode mode){SceneFlowToolbar.Open(true);return Result.Success;}
}
public sealed class SceneFlowUvToolsCommand:Command
{
    public override string EnglishName=>"RhinoSceneFlowUVTools";
    protected override Result RunCommand(RhinoDoc doc,RunMode mode){SceneFlowWorkspace.Open("uv");return Result.Success;}
}

using Rhino;
using Rhino.Commands;

namespace RhinoSceneFlow.Plugin;

public sealed class PanelCommand : Command
{
    public override string EnglishName=>"RhinoSceneFlowPanel";
    protected override Result RunCommand(RhinoDoc doc,RunMode mode)
    {
        try{ExportPanelController.Open(doc);return Result.Success;}
        catch(Exception ex){RhinoApp.WriteLine(ex.Message);return Result.Failure;}
    }
}

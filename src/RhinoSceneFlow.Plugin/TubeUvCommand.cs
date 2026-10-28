using Rhino;
using Rhino.Commands;
using Rhino.DocObjects;
using Rhino.Input.Custom;

namespace RhinoSceneFlow.Plugin;

public sealed class TubeUvCommand:Command
{
    public override string EnglishName=>"RhinoSceneFlowTubeUV";
    protected override Result RunCommand(RhinoDoc doc,RunMode mode)
    {
        try
        {
            var ids=MaterialSelection.Get(doc);if(ids.Length==0)return Result.Cancel;
            using var get=new GetObject();get.SetCommandPrompt("选择管体中心线（闭合或开放的等径管线）");get.GeometryFilter=ObjectType.Curve;get.EnablePreSelect(false,true);get.Get();
            if(get.CommandResult()!=Result.Success)return get.CommandResult();
            var job=UnwrapService.Start(doc,ids,null,"tube",get.Object(0).ObjectId);
            RhinoApp.WriteLine("管状连续 UV 任务已启动："+job.Id);return Result.Success;
        }
        catch(Exception e){RhinoApp.WriteLine(e.Message);return Result.Failure;}
    }
}

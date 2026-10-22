using Rhino;
using Rhino.Commands;
using Rhino.Input;

namespace RhinoSceneFlow.Plugin;

public sealed class ShadowVolumeExportCommand : Command
{
    public override string EnglishName => "RhinoSceneFlowExportShadowVolumePSD";

    protected override Result RunCommand(RhinoDoc doc, RunMode mode)
    {
        int width=2048;
        var result=RhinoGet.GetInteger("Shadow volume PSD width (pixels)",true,ref width,64,8192);
        if(result!=Result.Success)return result;
        string path=ExportService.NewDefaultPath();
        result=RhinoGet.GetString("Shadow PSD absolute path (Enter for default)",true,ref path);
        if(result!=Result.Success)return result;
        try
        {
            var report=ExportService.ExportShadow(doc,width,path.Trim('"'),backend:"volume");
            RhinoApp.WriteLine($"Shadow volume PSD: {report.Export.Width} x {report.Export.Height}, {report.Export.ElapsedMilliseconds} ms, empty={report.Empty}\n{report.Export.Path}");
            return Result.Success;
        }
        catch(Exception ex){RhinoApp.WriteLine($"RhinoSceneFlow shadow volume export failed: {ex.Message}");return Result.Failure;}
    }
}

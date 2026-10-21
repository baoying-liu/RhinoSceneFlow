using Rhino;
using Rhino.Commands;
using Rhino.Input;

namespace RhinoSceneFlow.Plugin;

public sealed class ShadowExportCommand : Command
{
    public override string EnglishName => "RhinoSceneFlowExportShadowPSD";

    protected override Result RunCommand(RhinoDoc doc, RunMode mode)
    {
        int width = 2048;
        var result = RhinoGet.GetInteger("Shadow PSD width (pixels)", true, ref width, 64, 8192);
        if (result != Result.Success) return result;
        string path = ExportService.NewDefaultPath();
        result = RhinoGet.GetString("Shadow PSD absolute path (Enter for default)", true, ref path);
        if (result != Result.Success) return result;
        try
        {
            var report = ExportService.ExportShadow(doc, width, path.Trim('"'));
            RhinoApp.WriteLine($"Shadow PSD: {report.Export.Width} x {report.Export.Height}, {report.Export.ElapsedMilliseconds} ms, light={report.LightSource}, empty={report.Empty}\n{report.Export.Path}");
            return Result.Success;
        }
        catch (Exception ex) { RhinoApp.WriteLine($"RhinoSceneFlow shadow export failed: {ex.Message}"); return Result.Failure; }
    }
}

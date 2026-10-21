using Rhino;
using Rhino.Commands;
using Rhino.Input;

namespace RhinoSceneFlow.Plugin;

public sealed class ExportCommand : Command
{
    public override string EnglishName => "RhinoSceneFlowExportPSD";

    protected override Result RunCommand(RhinoDoc doc, RunMode mode)
    {
        int width = 2048;
        var result = RhinoGet.GetInteger("PSD 输出宽度（像素，保持视图比例）", true, ref width, 64, 8192);
        if (result != Result.Success) return result;
        string path = ExportService.NewDefaultPath();
        result = RhinoGet.GetString("PSD 输出完整路径（回车使用默认目录）", true, ref path);
        if (result != Result.Success) return result;
        try
        {
            var report = ExportService.Export(doc, width, path.Trim('"'));
            RhinoApp.WriteLine($"已导出 {report.LayerCount} 个颜色图层，{report.Width} × {report.Height}，耗时 {report.ElapsedMilliseconds} ms。\n{report.Path}");
            foreach (var pair in report.Skipped) RhinoApp.WriteLine($"未导出对象：{pair.Key} × {pair.Value}");
            return Result.Success;
        }
        catch (Exception ex) { RhinoApp.WriteLine($"RhinoSceneFlow 导出失败：{ex.Message}"); return Result.Failure; }
    }
}
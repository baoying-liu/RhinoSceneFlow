using Eto.Forms;
using Rhino;
using Rhino.Commands;
using Rhino.Display;
using Rhino.DocObjects;
using Rhino.Geometry;
using Rhino.Input;
using RhinoPSD.Core;

namespace RhinoPSD.Plugin;

public sealed class ExportCommand : Rhino.Commands.Command
{
    public override string EnglishName => "RhinoPSDExport";

    protected override Result RunCommand(RhinoDoc doc, RunMode mode)
    {
        var view = doc.Views.ActiveView;
        if (view is null) return Result.Failure;
        if (view is RhinoPageView)
        { RhinoApp.WriteLine("RhinoPSD v0.1 仅支持模型视图，请先切换到模型视图。"); return Result.Failure; }
        var viewport = view.ActiveViewport;
        var clipping = new ObjectEnumeratorSettings { ObjectTypeFilter = ObjectType.ClipPlane, HiddenObjects = true, LockedObjects = true };
        if (doc.Objects.GetObjectList(clipping).Any(o => o.Geometry is ClippingPlaneSurface cp && cp.ViewportIds().Contains(viewport.Id)))
        { RhinoApp.WriteLine("当前视图关联了裁剪平面，v0.1 尚不支持；请使用未关联裁剪平面的视图。"); return Result.Failure; }

        int width = 2048;
        var input = RhinoGet.GetInteger("PSD 输出宽度（像素，保持视图比例）", true, ref width, 64, 8192);
        if (input != Result.Success) return input;
        int height = Math.Max(1, (int)Math.Round((double)width * viewport.Size.Height / Math.Max(1, viewport.Size.Width)));
        if ((long)width * height > 8_000_000 || height > 8192)
        { RhinoApp.WriteLine("输出上限为 800 万像素，每边不超过 8192，请降低宽度。"); return Result.Failure; }

        string path;
        if (mode == RunMode.Scripted)
        {
            path = "";
            input = RhinoGet.GetString("PSD 输出完整路径", false, ref path);
            if (input != Result.Success) return input;
            path = path.Trim('"');
        }
        else
        {
            using var dialog = new SaveFileDialog { Title = "按图层颜色导出 PSD", FileName = "RhinoPSD.psd" };
            dialog.Filters.Add(new FileFilter("Photoshop PSD", ".psd"));
            if (dialog.ShowDialog(Rhino.UI.RhinoEtoApp.MainWindow) != DialogResult.Ok) return Result.Cancel;
            path = dialog.FileName;
        }
        if (!string.Equals(Path.GetExtension(path), ".psd", StringComparison.OrdinalIgnoreCase))
        { RhinoApp.WriteLine("输出文件必须使用 .psd 扩展名。"); return Result.Failure; }

        using var cancellation = new CancellationTokenSource();
        void Escape(object? sender, EventArgs args) => cancellation.Cancel();
        RhinoApp.EscapeKeyPressed += Escape;
        try
        {
            RhinoApp.WriteLine($"RhinoPSD：生成 {width} × {height} 图层颜色色块，背景透明。曲线、文字、贴图和阴影不在 v0.1 范围内。");
            var reader = new SceneReader(doc, viewport, cancellation.Token);
            var image = FlatRasterizer.Render(width, height, reader.Groups, reader.Read(), cancellation.Token);
            int layers = PsdWriter.Save(path, image, cancellation.Token);
            RhinoApp.WriteLine($"已导出 {layers} 个颜色图层；{reader.MeshObjects} 个面对象，{reader.TriangleCount} 个三角形。\n{Path.GetFullPath(path)}");
            foreach (var pair in reader.Skipped)
                RhinoApp.WriteLine($"未导出对象：{pair.Key} × {pair.Value}");
            return Result.Success;
        }
        catch (OperationCanceledException) { RhinoApp.WriteLine("已取消导出。"); return Result.Cancel; }
        catch (Exception ex) { RhinoApp.WriteLine($"RhinoPSD 导出失败：{ex.Message}"); return Result.Failure; }
        finally { RhinoApp.EscapeKeyPressed -= Escape; }
    }
}

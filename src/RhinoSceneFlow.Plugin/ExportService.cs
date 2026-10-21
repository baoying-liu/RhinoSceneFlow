using System.Diagnostics;
using Rhino;
using Rhino.Display;
using Rhino.DocObjects;
using Rhino.Geometry;
using RhinoSceneFlow.Core;

namespace RhinoSceneFlow.Plugin;

public sealed record ExportReport(string Path, int Width, int Height, int LayerCount, string[] Layers,
    int MeshObjects, int Triangles, long FileBytes, long ElapsedMilliseconds, Dictionary<string, int> Skipped,
    uint Document, Guid ViewportId, string ViewName, string Projection, string[] Limitations);

/// <summary>UI-thread application service shared by commands and the Platform automation bridge.</summary>
public static class ExportService
{
    public static string NewDefaultPath() => System.IO.Path.Combine(SceneFlowPlugin.Instance.ExportDirectory,
        $"SceneFlow-{DateTime.Now:yyyyMMdd-HHmmss-fffffff}-{Guid.NewGuid().ToString("N")[..6]}.psd");

    public static ExportReport Export(RhinoDoc doc, int width = 2048, string? path = null,
        bool overwrite = false, Guid? expectedViewport = null, CancellationToken cancellation = default)
    {
        if (RhinoApp.InvokeRequired) throw new InvalidOperationException("Export must run on Rhino's UI thread.");
        var watch = Stopwatch.StartNew();
        var view = doc.Views.ActiveView ?? throw new InvalidOperationException("No active model view.");
        if (view is RhinoPageView) throw new NotSupportedException("Layout views are not supported.");
        var viewport = view.ActiveViewport;
        if (expectedViewport.HasValue && expectedViewport != viewport.Id)
            throw new InvalidOperationException("The active viewport changed; query status before exporting.");
        var clipping = new ObjectEnumeratorSettings { ObjectTypeFilter = ObjectType.ClipPlane, HiddenObjects = true, LockedObjects = true };
        if (doc.Objects.GetObjectList(clipping).Any(o => o.Geometry is ClippingPlaneSurface cp && cp.ViewportIds().Contains(viewport.Id)))
            throw new NotSupportedException("Views associated with clipping planes are not supported.");
        if (width is < 64 or > 8192) throw new ArgumentOutOfRangeException(nameof(width), "Width must be 64–8192 pixels.");
        if (viewport.Size.Width < 1 || viewport.Size.Height < 1) throw new InvalidOperationException("Viewport size is invalid.");
        int height = Math.Max(1, (int)Math.Round((double)width * viewport.Size.Height / viewport.Size.Width));
        if ((long)width * height > 8_000_000 || height > 8192)
            throw new ArgumentOutOfRangeException(nameof(width), "Output limit: 8 million pixels, maximum side 8192.");
        path ??= NewDefaultPath();
        if (!System.IO.Path.IsPathFullyQualified(path)) throw new ArgumentException("Output path must be absolute.");
        if (!string.Equals(System.IO.Path.GetExtension(path), ".psd", StringComparison.OrdinalIgnoreCase))
            throw new ArgumentException("Output must have a .psd extension.");
        path = System.IO.Path.GetFullPath(path);
        if (!overwrite && File.Exists(path)) throw new IOException("Output already exists; set overwrite=true explicitly.");
        var reader = new SceneReader(doc, viewport, cancellation);
        var image = FlatRasterizer.Render(width, height, reader.Groups, reader.Read(), cancellation);
        var visible = image.GetVisibleLayers(cancellation);
        if (visible.Count == 0) throw new InvalidOperationException("No visible surface pixels to export.");
        Directory.CreateDirectory(System.IO.Path.GetDirectoryName(path)!);
        int count = PsdWriter.Save(path, image, cancellation, overwrite);
        return new ExportReport(path, width, height, count, visible.Select(l => image.Groups[l.Group].Name).ToArray(),
            reader.MeshObjects, reader.TriangleCount, new FileInfo(path).Length, watch.ElapsedMilliseconds,
            reader.Skipped, doc.RuntimeSerialNumber, viewport.Id, viewport.Name,
            viewport.IsParallelProjection ? "parallel" : "perspective",
            ["Opaque layer-color surfaces only", "Textures, lighting and alpha materials are not exported", "Curves, text, annotations and hatches are skipped"]);
    }
}

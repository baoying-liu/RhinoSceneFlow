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
public sealed record ShadowExportReport(ExportReport Export, double[] ToSun, string LightSource, string Color, double Opacity, bool IncludeFormShading, double Bias, bool Empty);

public static class ExportService
{
    public static string NewDefaultPath() => System.IO.Path.Combine(SceneFlowPlugin.Instance.ExportDirectory,
        $"SceneFlow-{DateTime.Now:yyyyMMdd-HHmmss-fffffff}-{Guid.NewGuid().ToString("N")[..6]}.psd");

    public static ExportReport Export(RhinoDoc doc, int width = 2048, string? path = null,
        bool overwrite = false, Guid? expectedViewport = null, CancellationToken cancellation = default) =>
        ExportInternal(doc, width, path, overwrite, expectedViewport, cancellation, null);

    public static ShadowExportReport ExportShadow(RhinoDoc doc, int width = 2048, string? path = null,
        bool overwrite = false, Guid? expectedViewport = null, Vec3? toSun = null,
        Rgb? color = null, double opacity = 1, bool includeFormShading = false, double? bias = null)
    {
        if (RhinoApp.InvokeRequired) throw new InvalidOperationException("Export must run on Rhino UI thread.");
        var sun = doc.RenderSettings.Sun;
        var direction = sun.Vector;
        string source = toSun.HasValue ? "explicit" : sun.Enabled && direction.IsValid && direction.Length > 0 && direction.Z < 0 ? "rhino_sun" : "default";
        var light = (toSun ?? (source == "rhino_sun" ? new Vec3(-direction.X,-direction.Y,-direction.Z) : new Vec3(-1,-1,2))).Unit;
        // Bias is in model units and deliberately much smaller than document modeling tolerance.
        double epsilon = bias ?? Math.Max(doc.ModelAbsoluteTolerance * .001, 1e-7);
        var settings = new ShadowSettings(light, color ?? new Rgb(90,90,90), includeFormShading, epsilon, opacity);
        var report = ExportInternal(doc, width, path, overwrite, expectedViewport, default, settings);
        return new(report, [light.X,light.Y,light.Z], source, settings.Color.Hex, opacity, includeFormShading, epsilon, report.Layers.Length == 0);
    }

    private static ExportReport ExportInternal(RhinoDoc doc, int width, string? path, bool overwrite,
        Guid? expectedViewport, CancellationToken cancellation, ShadowSettings? shadow)
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
        var reader = new SceneReader(doc, viewport, cancellation, shadow is not null);
        var triangles = reader.Read().ToArray();
        var image = shadow is null ? FlatRasterizer.Render(width, height, reader.Groups, triangles, cancellation) :
            ShadowRenderer.Render(width, height, reader.Camera, reader.WorldTriangles, shadow, cancellation);
        var visible = image.GetVisibleLayers(cancellation);
        if (visible.Count == 0 && shadow is null) throw new InvalidOperationException("No visible surface pixels to export.");
        Directory.CreateDirectory(System.IO.Path.GetDirectoryName(path)!);
        int count = PsdWriter.Save(path, image, cancellation, overwrite, allowEmpty: shadow is not null);
        return new ExportReport(path, width, height, count, visible.Select(l => image.Groups[l.Group].Name).ToArray(),
            reader.MeshObjects, reader.TriangleCount, new FileInfo(path).Length, watch.ElapsedMilliseconds,
            reader.Skipped, doc.RuntimeSerialNumber, viewport.Id, viewport.Name,
            viewport.IsParallelProjection ? "parallel" : "perspective",
            shadow is not null ? ["Opaque mesh approximations; no alpha cutouts", "Existing visible surfaces receive shadows; no implicit ground plane", "Directional hard shadows; form shading optional"] : ["Opaque layer-color surfaces only", "Textures, lighting and alpha materials are not exported", "Curves, text, annotations and hatches are skipped"]);
    }
}

using Rhino;
using Rhino.Display;
using Rhino.DocObjects;
using Rhino.Geometry;
using RhinoSceneFlow.Core;

namespace RhinoSceneFlow.Plugin;

internal sealed class SceneReader(RhinoDoc doc, RhinoViewport viewport, CancellationToken cancellation)
{
    private readonly Dictionary<int, int> groupByColor = new();
    private readonly List<ColorGroup> groups = [];
    private readonly List<HashSet<string>> names = [];
    public IReadOnlyList<ColorGroup> Groups => groups;
    public Dictionary<string, int> Skipped { get; } = new();
    public int MeshObjects { get; private set; }
    public int TriangleCount { get; private set; }

    public IEnumerable<Triangle> Read()
    {
        if (!viewport.GetFrustum(out double l, out double r, out double b, out double t, out double n, out double f))
            throw new InvalidOperationException("无法读取当前视图相机。");
        var camera = new CameraProjection(ToVec(viewport.CameraLocation), ToVec(viewport.CameraX),
            ToVec(viewport.CameraY), ToVec(viewport.CameraZ), l, r, b, t, n, f, viewport.IsParallelProjection);
        var settings = new ObjectEnumeratorSettings
        {
            NormalObjects = true, LockedObjects = true, HiddenObjects = false,
            ReferenceObjects = true, IdefObjects = false, ViewportFilter = viewport,
            VisibleFilter = true
        };
        foreach (var obj in doc.Objects.GetObjectList(settings))
            foreach (var tri in Visit(obj, Transform.Identity, camera, 0)) yield return tri;
        for (int i = 0; i < groups.Count; i++)
        {
            string label = string.Join(" / ", names[i].OrderBy(s => s, StringComparer.Ordinal));
            if (label.Length > 180) label = label[..180] + "…";
            groups[i] = groups[i] with { Name = $"{groups[i].Color.Hex} {label}" };
        }
    }

    private IEnumerable<Triangle> Visit(RhinoObject obj, Transform transform, CameraProjection camera, int nesting)
    {
        cancellation.ThrowIfCancellationRequested();
        if (nesting > 32) throw new InvalidOperationException("块嵌套超过 32 层。");
        if (obj.IsHidden || !obj.Attributes.Visible || !LayerVisible(obj.Attributes.LayerIndex)) yield break;
        if (obj is InstanceObject instance)
        {
            foreach (var child in instance.InstanceDefinition.GetObjects())
                foreach (var tri in Visit(child, transform * instance.InstanceXform, camera, nesting + 1)) yield return tri;
            yield break;
        }
        int group = Group(obj.Attributes.LayerIndex);
        var geometry = obj.Geometry;
        Mesh[] meshes;
        bool owned = true;
        switch (geometry)
        {
            case Mesh mesh: meshes = [mesh]; owned = false; break;
            case Brep brep: meshes = MeshBrep(brep); break;
            case Extrusion extrusion:
                using (var eb = extrusion.ToBrep()) meshes = MeshBrep(eb);
                break;
            case SubD subd:
                var sm = Mesh.CreateFromSubD(subd, 2);
                meshes = sm is null ? [] : [sm]; break;
            case Surface surface:
                using (var sb = surface.ToBrep()) meshes = MeshBrep(sb);
                break;
            default:
                string type = obj.ObjectType.ToString();
                Skipped[type] = Skipped.GetValueOrDefault(type) + 1;
                yield break;
        }
        try
        {
            if (meshes.Length == 0) throw new InvalidOperationException($"对象 {obj.Id} 无法生成显示网格。");
            MeshObjects++;
            foreach (var mesh in meshes)
            {
                var vertices = new ClipVertex[mesh.Vertices.Count];
                for (int i = 0; i < vertices.Length; i++)
                {
                    var p = (Point3d)mesh.Vertices[i];
                    p.Transform(transform); vertices[i] = camera.Project(ToVec(p));
                }
                foreach (var face in mesh.Faces)
                {
                    TriangleCount++;
                    yield return new Triangle(vertices[face.A], vertices[face.B], vertices[face.C], group);
                    if (face.IsQuad)
                    {
                        TriangleCount++;
                        yield return new Triangle(vertices[face.A], vertices[face.C], vertices[face.D], group);
                    }
                }
            }
        }
        finally { if (owned) foreach (var mesh in meshes) mesh.Dispose(); }
    }

    private bool LayerVisible(int index)
    {
        var visited = new HashSet<Guid>();
        var layer = doc.Layers[index];
        while (layer is not null)
        {
            if (!visited.Add(layer.Id) || !layer.IsVisible || !layer.PerViewportIsVisible(viewport.Id)) return false;
            if (layer.ParentLayerId == Guid.Empty) break;
            layer = doc.Layers.FindId(layer.ParentLayerId);
        }
        return layer is not null;
    }

    private int Group(int index)
    {
        var layer = doc.Layers[index];
        var color = layer.Color; // Deliberately use the actual layer RGB, ignoring object/material colors.
        int key = (color.R << 16) | (color.G << 8) | color.B;
        if (!groupByColor.TryGetValue(key, out int group))
        {
            group = groups.Count; groupByColor.Add(key, group);
            groups.Add(new ColorGroup("", new Rgb(color.R, color.G, color.B))); names.Add([]);
        }
        names[group].Add(layer.FullPath);
        return group;
    }

    private static Vec3 ToVec(Point3d p) => new(p.X, p.Y, p.Z);
    private static Vec3 ToVec(Vector3d p) => new(p.X, p.Y, p.Z);

    private static Mesh[] MeshBrep(Brep brep)
    {
        using var parameters = MeshingParameters.QualityRenderMesh;
        // A bilinear saddle can otherwise be returned as one twisted quad. Splitting that
        // quad into two planar triangles changes the surface and its silhouette dramatically.
        parameters.GridMinCount = Math.Max(64, parameters.GridMinCount);
        parameters.RefineGrid = true;
        parameters.SimplePlanes = true;
        return Mesh.CreateFromBrep(brep, parameters) ?? [];
    }
}

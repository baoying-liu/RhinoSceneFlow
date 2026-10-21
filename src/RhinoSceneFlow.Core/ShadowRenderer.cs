using g3;

namespace RhinoSceneFlow.Core;

public sealed record ShadowSettings(Vec3 ToSun, Rgb Color, bool IncludeFormShading = false, double Bias = 0.00001, double Opacity = 1);

/// <summary>Directional hard shadows on the nearest visible mesh surface. No ambient occlusion or gradients.</summary>
public static class ShadowRenderer
{
    public static RasterImage Render(int width, int height, CameraProjection camera,
        IReadOnlyList<WorldTriangle> triangles, ShadowSettings settings, CancellationToken cancellation = default)
    {
        if (width < 1 || height < 1 || width > 8192 || height > 8192 || (long)width * height > 8_000_000)
            throw new ArgumentOutOfRangeException(nameof(width));
        if (!(settings.Bias > 0) || !double.IsFinite(settings.Bias)) throw new ArgumentException("Bias must be finite and positive.");
        if (!(settings.Opacity > 0 && settings.Opacity <= 1)) throw new ArgumentException("Opacity must be greater than 0 and at most 1.");
        var sun = ToG(settings.ToSun.Unit);
        // Local coordinates preserve precision in georeferenced models. Independent vertices also
        // allow overlapping, disconnected and nonmanifold Rhino meshes without topology repair.
        var mesh = new DMesh3();
        var shadingNormals = new List<(Vec3? A, Vec3? B, Vec3? C)>();
        foreach (var t in triangles)
        {
            cancellation.ThrowIfCancellationRequested();
            var a = ToG(t.A - camera.Origin); var b = ToG(t.B - camera.Origin); var c = ToG(t.C - camera.Origin);
            if (!a.IsFinite || !b.IsFinite || !c.IsFinite || (b-a).Cross(c-a).LengthSquared < 1e-28) continue;
            int ia = mesh.AppendVertex(a), ib = mesh.AppendVertex(b), ic = mesh.AppendVertex(c);
            mesh.AppendTriangle(ia, ib, ic);
            shadingNormals.Add((t.NA,t.NB,t.NC));
        }
        var owners = new int[checked(width * height * 4)]; Array.Fill(owners, -1);
        if (mesh.TriangleCount == 0) return new(width, height, [new("Shadow", settings.Color)], owners, settings.Opacity);
        var tree = new DMeshAABBTree3(mesh, true);
        Parallel.For(0, height * 2, new ParallelOptions { CancellationToken = cancellation }, y =>
        {
            for (int x = 0; x < width * 2; x++)
            {
                if ((x & 127) == 0) cancellation.ThrowIfCancellationRequested();
                double u = (x + .5) / (width * 2), v = 1 - (y + .5) / (height * 2);
                var near = ToG(camera.At(u,v,camera.Near) - camera.Origin);
                var far = ToG(camera.At(u,v,camera.Far) - camera.Origin);
                var delta = far - near; double length = delta.Normalize();
                var ray = new Ray3d(near, delta);
                int id = tree.FindNearestHitTriangle(ray, length);
                if (id < 0) continue;
                var hit = MeshQueries.TriangleIntersection(mesh, id, ray);
                var point = ray.PointAt(hit.RayParameter);
                var geometricNormal = mesh.GetTriNormal(id);
                var normal = geometricNormal;
                var sn = shadingNormals[id];
                double normalOffset = settings.Bias;
                if (sn.A.HasValue && sn.B.HasValue && sn.C.HasValue)
                {
                    var bary = hit.TriangleBaryCoords;
                    var smooth = ToG(sn.A.Value * bary.x + sn.B.Value * bary.y + sn.C.Value * bary.z);
                    if (smooth.Normalize() > 0) normal = smooth.Dot(geometricNormal) < 0 ? -smooth : smooth;
                    // Bound local chord error using the three smooth tangent planes. Start
                    // above this faceted envelope to prevent a smooth lit surface shadowing
                    // itself at the terminator. This is geometry-aware bias, not image cleanup.
                    var vertices = mesh.GetTriangle(id);
                    normalOffset += Math.Max(Math.Abs((point-mesh.GetVertex(vertices.a)).Dot(ToG(sn.A.Value))),
                        Math.Max(Math.Abs((point-mesh.GetVertex(vertices.b)).Dot(ToG(sn.B.Value))),
                            Math.Abs((point-mesh.GetVertex(vertices.c)).Dot(ToG(sn.C.Value)))));
                }
                // Orient an opaque two-sided surface toward the viewer. Backlighting is form
                // shading, separately requested; it must not become an accidental cast shadow.
                if (normal.Dot(delta) > 0) normal = -normal;
                bool backlit = normal.Dot(sun) <= 1e-10;
                bool shadow = backlit ? settings.IncludeFormShading :
                    tree.FindNearestHitTriangle(new Ray3d(point + normal * normalOffset + sun * settings.Bias, sun)) >= 0;
                if (shadow) owners[y * width * 2 + x] = 0;
            }
        });
        return new(width, height, [new("Shadow", settings.Color)], owners, settings.Opacity);
    }

    private static Vector3d ToG(Vec3 p) => new(p.X,p.Y,p.Z);
}

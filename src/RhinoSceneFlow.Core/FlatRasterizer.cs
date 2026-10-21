namespace RhinoSceneFlow.Core;

/// <summary>Opaque, double-sided triangles with a shared depth buffer for all color groups.</summary>
public static class FlatRasterizer
{
    public static RasterImage Render(int width, int height, IReadOnlyList<ColorGroup> groups,
        IEnumerable<Triangle> triangles, CancellationToken cancellation = default)
    {
        if (width < 1 || height < 1 || width > 8192 || height > 8192 || (long)width * height > 8_000_000)
            throw new ArgumentOutOfRangeException(nameof(width), "Output must contain at most 8 million pixels (each side <= 8192).");
        int sw = checked(width * 2), sh = checked(height * 2);
        var owners = new int[checked(sw * sh)];
        Array.Fill(owners, -1);
        var depth = new double[owners.Length];
        Array.Fill(depth, double.PositiveInfinity);
        foreach (var triangle in triangles)
        {
            cancellation.ThrowIfCancellationRequested();
            if (triangle.Group < 0 || triangle.Group >= groups.Count) throw new ArgumentException("Unknown color group.");
            if (!triangle.A.IsFinite || !triangle.B.IsFinite || !triangle.C.IsFinite) continue;
            var polygon = new List<ClipVertex> { triangle.A, triangle.B, triangle.C };
            for (int plane = 0; plane < 6 && polygon.Count > 0; plane++) polygon = Clip(polygon, plane);
            for (int i = 1; i + 1 < polygon.Count; i++)
                Draw(polygon[0], polygon[i], polygon[i + 1], triangle.Group, sw, sh, owners, depth, cancellation);
        }
        return new RasterImage(width, height, groups, owners);
    }

    private static double Distance(ClipVertex v, int plane) => plane switch
    {
        0 => v.X + v.W, 1 => v.W - v.X, 2 => v.Y + v.W,
        3 => v.W - v.Y, 4 => v.Z, _ => v.W - v.Z
    };

    private static List<ClipVertex> Clip(List<ClipVertex> input, int plane)
    {
        var result = new List<ClipVertex>(input.Count + 1);
        var previous = input[^1];
        double pd = Distance(previous, plane);
        foreach (var current in input)
        {
            double cd = Distance(current, plane);
            if ((pd >= 0) != (cd >= 0)) result.Add(ClipVertex.Lerp(previous, current, pd / (pd - cd)));
            if (cd >= 0) result.Add(current);
            previous = current;
            pd = cd;
        }
        return result;
    }

    private readonly record struct Screen(double X, double Y, double Z);
    private static double Edge(Screen a, Screen b, double x, double y) =>
        (b.X - a.X) * (y - a.Y) - (b.Y - a.Y) * (x - a.X);

    private static void Draw(ClipVertex ca, ClipVertex cb, ClipVertex cc, int group,
        int width, int height, int[] owners, double[] depth, CancellationToken cancellation)
    {
        if (ca.W <= 0 || cb.W <= 0 || cc.W <= 0) return;
        Screen Project(ClipVertex v) => new((v.X / v.W + 1) * width / 2,
            (1 - v.Y / v.W) * height / 2, v.Z / v.W);
        var a = Project(ca); var b = Project(cb); var c = Project(cc);
        double area = Edge(a, b, c.X, c.Y);
        if (Math.Abs(area) < 1e-12) return;
        if (area < 0) { (b, c) = (c, b); area = -area; }
        int x0 = Math.Max(0, (int)Math.Floor(Math.Min(a.X, Math.Min(b.X, c.X))));
        int x1 = Math.Min(width - 1, (int)Math.Ceiling(Math.Max(a.X, Math.Max(b.X, c.X))));
        int y0 = Math.Max(0, (int)Math.Floor(Math.Min(a.Y, Math.Min(b.Y, c.Y))));
        int y1 = Math.Min(height - 1, (int)Math.Ceiling(Math.Max(a.Y, Math.Max(b.Y, c.Y))));
        for (int y = y0; y <= y1; y++)
        {
            cancellation.ThrowIfCancellationRequested();
            for (int x = x0; x <= x1; x++)
            {
                double wa = Edge(b, c, x + .5, y + .5), wb = Edge(c, a, x + .5, y + .5), wc = Edge(a, b, x + .5, y + .5);
                if (wa < -1e-9 || wb < -1e-9 || wc < -1e-9) continue;
                double z = (wa * a.Z + wb * b.Z + wc * c.Z) / area;
                int index = y * width + x;
                // Stable color-group tie break prevents coplanar results depending on object enumeration.
                if (z < depth[index] - 1e-12 || (Math.Abs(z - depth[index]) <= 1e-12 && group < owners[index]))
                { depth[index] = z; owners[index] = group; }
            }
        }
    }
}

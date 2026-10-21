namespace RhinoPSD.Core;

public readonly record struct Rgb(byte R, byte G, byte B)
{
    public string Hex => $"#{R:X2}{G:X2}{B:X2}";
}

public sealed record ColorGroup(string Name, Rgb Color);
public readonly record struct Vec3(double X, double Y, double Z)
{
    public static Vec3 operator -(Vec3 a, Vec3 b) => new(a.X - b.X, a.Y - b.Y, a.Z - b.Z);
    public double Dot(Vec3 b) => X * b.X + Y * b.Y + Z * b.Z;
}

// Homogeneous clip space: -W <= X,Y <= W, 0 <= Z <= W.
public readonly record struct ClipVertex(double X, double Y, double Z, double W)
{
    public bool IsFinite => double.IsFinite(X) && double.IsFinite(Y) && double.IsFinite(Z) && double.IsFinite(W);
    public static ClipVertex Lerp(ClipVertex a, ClipVertex b, double t) =>
        new(a.X + (b.X - a.X) * t, a.Y + (b.Y - a.Y) * t,
            a.Z + (b.Z - a.Z) * t, a.W + (b.W - a.W) * t);
}

public readonly record struct Triangle(ClipVertex A, ClipVertex B, ClipVertex C, int Group);

public sealed record CameraProjection(Vec3 Origin, Vec3 Right, Vec3 Up, Vec3 Back,
    double Left, double RightEdge, double Bottom, double Top, double Near, double Far, bool Parallel)
{
    public ClipVertex Project(Vec3 world)
    {
        var p = world - Origin;
        double x = p.Dot(Right), y = p.Dot(Up), d = -p.Dot(Back);
        if (Parallel)
            return new((2 * x - RightEdge - Left) / (RightEdge - Left),
                (2 * y - Top - Bottom) / (Top - Bottom), (d - Near) / (Far - Near), 1);
        return new((2 * Near * x - (RightEdge + Left) * d) / (RightEdge - Left),
            (2 * Near * y - (Top + Bottom) * d) / (Top - Bottom),
            Far / (Far - Near) * (d - Near), d);
    }
}

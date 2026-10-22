namespace RhinoSceneFlow.Core;

public sealed record LayerBounds(int Group, int Left, int Top, int Right, int Bottom)
{
    public int Width => Right - Left;
    public int Height => Bottom - Top;
}

public sealed class RasterImage : IPsdImage
{
    private readonly int[] owners;
    private readonly double opacity;
    public int Width { get; }
    public int Height { get; }
    public IReadOnlyList<ColorGroup> Groups { get; }

    internal RasterImage(int width, int height, IReadOnlyList<ColorGroup> groups, int[] owners, double opacity = 1)
    { Width = width; Height = height; Groups = groups; this.owners = owners; this.opacity = opacity; }

    public int SampleOwner(int x, int y, int sample) =>
        owners[(y * 2 + sample / 2) * Width * 2 + x * 2 + sample % 2];

    public IReadOnlyList<LayerBounds> GetVisibleLayers(CancellationToken cancellation = default)
    {
        var left = Enumerable.Repeat(Width, Groups.Count).ToArray();
        var top = Enumerable.Repeat(Height, Groups.Count).ToArray();
        var right = new int[Groups.Count]; var bottom = new int[Groups.Count];
        for (int y = 0; y < Height; y++)
        {
            cancellation.ThrowIfCancellationRequested();
            for (int x = 0; x < Width; x++)
                for (int s = 0; s < 4; s++)
                {
                    int g = SampleOwner(x, y, s);
                    if (g < 0) continue;
                    left[g] = Math.Min(left[g], x); top[g] = Math.Min(top[g], y);
                    right[g] = Math.Max(right[g], x + 1); bottom[g] = Math.Max(bottom[g], y + 1);
                }
        }
        return Enumerable.Range(0, Groups.Count).Where(g => right[g] > left[g])
            .Select(g => new LayerBounds(g, left[g], top[g], right[g], bottom[g])).ToArray();
    }

    // Conditional coverage accounts for layers above this one. It prevents dark seams when
    // adjacent antialiased color groups are composited with Photoshop's normal alpha blending.
    public byte LayerAlpha(int group, int x, int y)
    {
        int own = 0, above = 0;
        for (int s = 0; s < 4; s++)
        {
            int g = SampleOwner(x, y, s);
            if (g == group) own++;
            else if (g >= 0 && g < group) above++;
        }
        return own == 0 ? (byte)0 : (byte)Math.Round(opacity * 255.0 * own / (4 - above));
    }

    public byte CompositeChannel(int channel, int x, int y)
    {
        int sum = 0, covered = 0;
        for (int s = 0; s < 4; s++)
        {
            int g = SampleOwner(x, y, s);
            if (g < 0) continue;
            covered++;
            var color = Groups[g].Color;
            sum += channel switch { 0 => color.R, 1 => color.G, 2 => color.B, _ => 0 };
        }
        if (channel == 3) return (byte)Math.Round(opacity * 255.0 * covered / 4);
        return covered == 0 ? (byte)0 : (byte)Math.Round((double)sum / covered);
    }
}

using RhinoPSD.Core;

static void Check(bool condition, string message)
{ if (!condition) throw new Exception(message); }
static ClipVertex V(double x, double y, double z = .6, double w = 1) => new(x, y, z, w);
static IEnumerable<Triangle> Quad(int group, double z, double left = -.8, double right = .8)
{
    yield return new(V(left, -.8, z), V(right, -.8, z), V(right, .8, z), group);
    yield return new(V(left, -.8, z), V(right, .8, z), V(left, .8, z), group);
}
var groups = new[] {
    new ColorGroup("#E65032 建筑 / 墙面", new Rgb(230, 80, 50)),
    new ColorGroup("#3282C8 铺装", new Rgb(50, 130, 200)),
    new ColorGroup("hidden", new Rgb(0, 255, 0))
};
var geometry = Quad(1, .7).Concat(Quad(0, .2, -.3, .3)).Concat(Quad(2, .9)).ToArray();
var image = FlatRasterizer.Render(96, 64, groups, geometry);
Check(image.SampleOwner(48, 32, 0) == 0, "Foreground must occlude background.");
Check(image.SampleOwner(15, 32, 0) == 1, "Exposed background must remain.");
Check(image.CompositeChannel(3, 0, 0) == 0, "Background must be transparent.");
Check(image.GetVisibleLayers().Count == 2, "Fully occluded groups must not create layers.");
var reverse = FlatRasterizer.Render(96, 64, groups, geometry.Reverse());
for (int y = 0; y < 64; y++) for (int x = 0; x < 96; x++) for (int s = 0; s < 4; s++)
    Check(image.SampleOwner(x, y, s) == reverse.SampleOwner(x, y, s), "Depth must be independent of draw order.");

var cut = FlatRasterizer.Render(32, 32, groups, [new(V(-2, -.5, -.5), V(.8, -.5, .5), V(0, .8, .5), 0)]);
Check(cut.GetVisibleLayers().Count == 1, "Near/side-plane crossing triangles must be clipped, not discarded.");
var behind = FlatRasterizer.Render(32, 32, groups, [new(V(-.5, -.5, -.2), V(.5, -.5, -.2), V(0, .5, -.2), 0)]);
Check(behind.GetVisibleLayers().Count == 0, "Geometry behind near plane must be excluded.");
var perspective = new CameraProjection(new(0, 0, 0), new(1, 0, 0), new(0, 1, 0), new(0, 0, 1), -1, 1, -1, 1, 1, 100, false);
Check(Math.Abs(perspective.Project(new(0, 0, -1)).Z) < 1e-10, "Perspective near plane.");
var far = perspective.Project(new(0, 0, -100));
Check(Math.Abs(far.Z / far.W - 1) < 1e-10, "Perspective far plane.");
Check(Math.Abs(perspective.Project(new(2, 0, -2)).X / 2 - 1) < 1e-10, "Perspective frustum edge.");

// Fractional coverage across adjacent groups must reconstruct the supersampled composite.
var diagonal = FlatRasterizer.Render(97, 65, groups,
    Quad(1, .8, -1, 1).Concat([new Triangle(V(-.9, -.7, .2), V(.9, -.4, .2), V(-.4, .9, .2), 0)]));
for (int y = 0; y < diagonal.Height; y++) for (int x = 0; x < diagonal.Width; x++)
{
    double alpha = 0; var premul = new double[3];
    for (int g = groups.Length - 1; g >= 0; g--)
    {
        double a = diagonal.LayerAlpha(g, x, y) / 255.0;
        var color = groups[g].Color;
        byte[] channels = [color.R, color.G, color.B];
        for (int c = 0; c < 3; c++) premul[c] = channels[c] * a + premul[c] * (1 - a);
        alpha = a + alpha * (1 - a);
    }
    Check(Math.Abs(alpha * 255 - diagonal.CompositeChannel(3, x, y)) <= 1.1, "Composite alpha mismatch.");
    if (alpha > 0) for (int c = 0; c < 3; c++)
        Check(Math.Abs(premul[c] / alpha - diagonal.CompositeChannel(c, x, y)) <= 1.1, "Composite color mismatch.");
}

string output = Path.GetFullPath(args.Length > 0 ? args[0] : "artifacts/validation");
Directory.CreateDirectory(output);
Check(PsdWriter.Save(Path.Combine(output, "occlusion.psd"), image) == 2, "PSD visible layer count.");
PsdWriter.Save(Path.Combine(output, "antialias.psd"), diagonal);
// An independent decoder compares against this reference, not against our PSD reader.
using (var raw = File.Create(Path.Combine(output, "antialias.rgba")))
    for (int y = 0; y < diagonal.Height; y++) for (int x = 0; x < diagonal.Width; x++)
        for (int c = 0; c < 4; c++) raw.WriteByte(diagonal.CompositeChannel(c, x, y));
byte[] original = File.ReadAllBytes(Path.Combine(output, "occlusion.psd"));
using var canceled = new CancellationTokenSource(); canceled.Cancel();
try { PsdWriter.Save(Path.Combine(output, "occlusion.psd"), image, canceled.Token); throw new Exception("Cancellation ignored."); }
catch (OperationCanceledException) { }
Check(original.SequenceEqual(File.ReadAllBytes(Path.Combine(output, "occlusion.psd"))), "Cancellation must preserve existing output.");
Console.WriteLine($"PASS: occlusion, clipping, projection, alpha composition, PSD export, cancellation. Fixtures: {output}");

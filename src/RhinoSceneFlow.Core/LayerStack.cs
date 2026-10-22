namespace RhinoSceneFlow.Core;

public interface IPsdImage
{
    int Width { get; }
    int Height { get; }
    IReadOnlyList<ColorGroup> Groups { get; }
    IReadOnlyList<LayerBounds> GetVisibleLayers(CancellationToken cancellation = default);
    byte LayerAlpha(int group,int x,int y);
    byte CompositeChannel(int channel,int x,int y);
}

/// <summary>Independent image passes, top to bottom. Keeps each pass's pixel layers
/// and computes the same normal-alpha composite that a PSD editor will display.</summary>
public sealed class LayerStack : IPsdImage
{
    private readonly RasterImage[] passes;
    private readonly (RasterImage Image,int Group)[] layers;
    public int Width => passes[0].Width;
    public int Height => passes[0].Height;
    public IReadOnlyList<ColorGroup> Groups { get; }
    public LayerStack(params RasterImage[] topToBottom)
    {
        if(topToBottom.Length==0)throw new ArgumentException("Select at least one image pass.");
        passes=topToBottom;
        if(passes.Any(p=>p.Width!=Width||p.Height!=Height))throw new ArgumentException("Pass dimensions must match.");
        layers=passes.SelectMany(p=>Enumerable.Range(0,p.Groups.Count).Select(g=>(p,g))).ToArray();
        Groups=layers.Select(l=>l.Image.Groups[l.Group]).ToArray();
    }
    public IReadOnlyList<LayerBounds> GetVisibleLayers(CancellationToken cancellation = default)
    {
        var result=new List<LayerBounds>();int offset=0;
        foreach(var image in passes)
        {
            var visible=image.GetVisibleLayers(cancellation);
            if(visible.Count==0 && image.Groups.Count==1)
                result.Add(new(offset,0,0,1,1)); // Keep a selected empty shadow pass.
            else result.AddRange(visible.Select(l=>l with {Group=l.Group+offset}));
            offset+=image.Groups.Count;
        }
        return result;
    }
    public byte LayerAlpha(int group,int x,int y)=>layers[group].Image.LayerAlpha(layers[group].Group,x,y);
    public byte CompositeChannel(int channel,int x,int y)
    {
        double alpha=0,color=0;
        foreach(var image in passes)
        {
            double weight=image.CompositeChannel(3,x,y)/255.0*(1-alpha);
            if(channel<3)color+=image.CompositeChannel(channel,x,y)*weight;
            alpha+=weight;
        }
        return channel==3?(byte)Math.Round(alpha*255):alpha==0?(byte)0:(byte)Math.Round(color/alpha);
    }
}

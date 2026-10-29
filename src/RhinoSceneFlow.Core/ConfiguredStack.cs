namespace RhinoSceneFlow.Core;

public sealed record StyledPass(string Name,IPsdImage Image,string Blend="norm",byte Opacity=255,bool Folder=false);

/// <summary>Top-to-bottom isolated passes, with genuine PSD blend/opacity metadata.</summary>
public sealed class ConfiguredStack : IPsdImage,IPsdHierarchy
{
    public static readonly string[] BlendKeys=["norm","mul ","scrn","over","dark","lite"];
    private readonly StyledPass[] passes;
    private readonly (IPsdImage Image,int Group)[] layers;
    private int cachedY=-1;
    private readonly byte[] composite;
    private readonly double[] accumulated;
    private readonly byte[] sourceRow;
    public int Width=>passes[0].Image.Width;
    public int Height=>passes[0].Image.Height;
    public IReadOnlyList<ColorGroup> Groups{get;}
    public ConfiguredStack(params StyledPass[] topToBottom)
    {
        if(topToBottom.Length==0)throw new ArgumentException("Select at least one layer.");
        passes=topToBottom;
        if(passes.Any(p=>p.Image.Width!=Width||p.Image.Height!=Height||!BlendKeys.Contains(p.Blend)))throw new ArgumentException("Invalid layer dimensions or blend mode.");
        layers=passes.SelectMany(p=>Enumerable.Range(0,p.Image.Groups.Count).Select(g=>(p.Image,g))).ToArray();
        Groups=layers.Select(l=>l.Image.Groups[l.Group]).ToArray();composite=new byte[Width*4];accumulated=new double[Width*4];sourceRow=new byte[Width*4];
    }
    public IReadOnlyList<LayerBounds> GetVisibleLayers(CancellationToken cancellation=default)
    {
        var result=new List<LayerBounds>();int offset=0;
        foreach(var pass in passes)
        {
            var visible=pass.Image.GetVisibleLayers(cancellation);
            if(visible.Count==0&&pass.Image.Groups.Count==1)result.Add(new(offset,0,0,1,1));
            else result.AddRange(visible.Select(b=>b with{Group=b.Group+offset}));
            offset+=pass.Image.Groups.Count;
        }
        return result;
    }
    public IReadOnlyList<PsdRecord> Records(CancellationToken cancellation=default)
    {
        var result=new List<PsdRecord>();int offset=0;
        foreach(var pass in passes)
        {
            var visible=pass.Image.GetVisibleLayers(cancellation);
            if(visible.Count==0)visible=[new(0,0,0,1,1)];
            if(pass.Folder)result.Add(new(new(-1,0,0,0,0),pass.Name,pass.Blend,pass.Opacity,1));
            if(pass.Image is IPsdHierarchy hierarchy)
                result.AddRange(hierarchy.Records(cancellation).Select(r=>r with{Bounds=r.Bounds.Group<0?r.Bounds:r.Bounds with{Group=r.Bounds.Group+offset}}));
            else
            foreach(var b in visible)
                result.Add(new(b with{Group=b.Group+offset},pass.Folder?pass.Image.Groups[b.Group].Name:pass.Name,
                    pass.Folder?"norm":pass.Blend,pass.Folder?(byte)255:pass.Opacity));
            if(pass.Folder)result.Add(new(new(-1,0,0,0,0),"</Layer group>",Section:3));
            offset+=pass.Image.Groups.Count;
        }
        return result;
    }
    public byte LayerAlpha(int group,int x,int y)=>layers[group].Image.LayerAlpha(layers[group].Group,x,y);
    public byte LayerChannel(int group,int channel,int x,int y)=>layers[group].Image.LayerChannel(layers[group].Group,channel,x,y);
    public void ReadLayerRow(int group,int channel,int y,int left,Span<byte> row)=>layers[group].Image.ReadLayerRow(layers[group].Group,channel,y,left,row);
    private static double Blend(string key,double b,double s)=>key switch
    {"mul "=>b*s,"scrn"=>b+s-b*s,"over"=>b<=.5?2*b*s:1-2*(1-b)*(1-s),"dark"=>Math.Min(b,s),"lite"=>Math.Max(b,s),_=>s};
    private void Composite(int y)
    {
        if(cachedY==y)return;
        var rgba=accumulated;Array.Clear(rgba);var source=sourceRow;
        foreach(var pass in Enumerable.Reverse(passes))
        {
            for(int c=0;c<4;c++)pass.Image.ReadCompositeRow(c,y,source.AsSpan(c*Width,Width));
            for(int x=0;x<Width;x++)
            {
                double a=source[3*Width+x]/255.0*pass.Opacity/255,ab=rgba[3*Width+x],outA=a+ab*(1-a);
                for(int c=0;c<3;c++)
                {
                    double b=rgba[c*Width+x],s=source[c*Width+x]/255.0;
                    rgba[c*Width+x]=outA==0?0:((1-a)*ab*b+(1-ab)*a*s+a*ab*Blend(pass.Blend,b,s))/outA;
                }
                rgba[3*Width+x]=outA;
            }
        }
        for(int i=0;i<composite.Length;i++)composite[i]=(byte)Math.Clamp(Math.Round(rgba[i]*255),0,255);
        cachedY=y;
    }
    public byte CompositeChannel(int channel,int x,int y){Composite(y);return composite[channel*Width+x];}
    public void ReadCompositeRow(int channel,int y,Span<byte> row){Composite(y);composite.AsSpan(channel*Width,row.Length).CopyTo(row);}
}

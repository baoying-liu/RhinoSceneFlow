namespace RhinoSceneFlow.Core;

/// <summary>Artistic emission multiplier, not calibrated luminance.</summary>
public sealed class EmissionSettings
{
    public bool Enabled {get;set;}
    public string Color {get;set;}="#FFF0D0";
    public double Intensity {get;set;}=1;
    [System.Text.Json.Serialization.JsonIgnore]
    public Rgb Rgb=>Parse(Color);
    public static Rgb Parse(string value)
    {
        if(value==null||value.Length!=7||value[0]!='#'||!uint.TryParse(value.AsSpan(1),System.Globalization.NumberStyles.HexNumber,null,out var n))throw new ArgumentException("Emission color must be #RRGGBB.");
        return new((byte)(n>>16),(byte)(n>>8),(byte)n);
    }
    public void Validate(){Parse(Color);if(!double.IsFinite(Intensity)||Intensity<0||Intensity>100)throw new ArgumentException("Emission intensity must be 0–100.");}
}

public sealed class CompositeOnlyImage(IPsdImage source,string name) : IPsdImage
{
    public int Width=>source.Width;public int Height=>source.Height;
    public IReadOnlyList<ColorGroup> Groups{get;}=[new(name,new(0,0,0))];
    public IReadOnlyList<LayerBounds> GetVisibleLayers(CancellationToken cancellation=default)
    {
        var bounds=source.GetVisibleLayers(cancellation);return bounds.Count==0?[]:[new(0,bounds.Min(b=>b.Left),bounds.Min(b=>b.Top),bounds.Max(b=>b.Right),bounds.Max(b=>b.Bottom))];
    }
    public byte LayerAlpha(int group,int x,int y)=>source.CompositeChannel(3,x,y);
    public byte LayerChannel(int group,int channel,int x,int y)=>source.CompositeChannel(channel,x,y);
    public byte CompositeChannel(int channel,int x,int y)=>source.CompositeChannel(channel,x,y);
    public void ReadLayerRow(int group,int channel,int y,int left,Span<byte> row){for(int x=0;x<row.Length;x++)row[x]=source.CompositeChannel(channel,left+x,y);}
    public void ReadCompositeRow(int channel,int y,Span<byte> row)=>source.ReadCompositeRow(channel,y,row);
}

/// <summary>Premultiplied, three-pass box bloom. Called on bounded halo tiles only.</summary>
public sealed class EmissionGlow : IPsdImage
{
    private readonly byte[][] data;
    private readonly LayerBounds[] footprints;
    public int Width{get;} public int Height{get;}
    public IReadOnlyList<ColorGroup> Groups{get;}
    public EmissionGlow(IPsdImage source,int radius,CancellationToken token=default)
    {
        Width=source.Width;Height=source.Height;Groups=source.Groups;
        if(radius<1||radius>64||(long)Width*Height>2_000_000)throw new ArgumentException("Invalid bloom tile.");
        data=new byte[Groups.Count][];footprints=new LayerBounds[Groups.Count];var visible=source.GetVisibleLayers(token).ToDictionary(b=>b.Group);
        for(int g=0;g<Groups.Count;g++)
        {
            token.ThrowIfCancellationRequested();
            if(!visible.TryGetValue(g,out var bounds)){data[g]=[];footprints[g]=new(g,0,0,0,0);continue;}
            var box=new LayerBounds(g,Math.Max(0,bounds.Left-3*radius),Math.Max(0,bounds.Top-3*radius),Math.Min(Width,bounds.Right+3*radius),Math.Min(Height,bounds.Bottom+3*radius));footprints[g]=box;
            int bw=box.Width,bh=box.Height,size=bw*bh;var a=new float[size*4];var b=new float[a.Length];var row=new byte[bw];
            for(int c=3;c>=0;c--)for(int y=0;y<bh;y++)
            {
                token.ThrowIfCancellationRequested();source.ReadLayerRow(g,c,y+box.Top,box.Left,row);
                for(int x=0;x<bw;x++){int i=(y*bw+x)*4;a[i+c]=c==3?row[x]/255f:row[x]/255f*a[i+3];}
            }
            for(int pass=0;pass<3;pass++){Blur(a,b,true);Blur(b,a,false);}
            var rgba=new byte[size*4];data[g]=rgba;
            for(int i=0;i<size;i++)
            {
                float alpha=a[i*4+3];rgba[i*4+3]=(byte)Math.Clamp(Math.Round(alpha*255*.65),0,255);
                for(int c=0;c<3;c++)rgba[i*4+c]=(byte)Math.Clamp(Math.Round(alpha>1e-8?a[i*4+c]/alpha*255:0),0,255);
            }
            void Blur(float[] input,float[] output,bool horizontal)
            {
                int lines=horizontal?bh:bw,length=horizontal?bw:bh;float divisor=2*radius+1;
                for(int line=0;line<lines;line++)
                {
                    token.ThrowIfCancellationRequested();
                    for(int c=0;c<4;c++)
                    {
                        int Index(int p)=>((horizontal?line*bw+p:p*bw+line)*4)+c;
                        float sum=0;for(int k=0;k<=radius&&k<length;k++)sum+=input[Index(k)];
                        for(int p=0;p<length;p++){output[Index(p)]=sum/divisor;if(p-radius>=0)sum-=input[Index(p-radius)];if(p+radius+1<length)sum+=input[Index(p+radius+1)];}
                    }
                }
            }
        }
    }
    public IReadOnlyList<LayerBounds> GetVisibleLayers(CancellationToken cancellation=default)
    {
        var result=new List<LayerBounds>();for(int g=0;g<data.Length;g++){int l=Width,t=Height,r=0,b=0;for(int y=0;y<Height;y++){cancellation.ThrowIfCancellationRequested();for(int x=0;x<Width;x++)if(LayerAlpha(g,x,y)>0){l=Math.Min(l,x);t=Math.Min(t,y);r=Math.Max(r,x+1);b=Math.Max(b,y+1);}}if(r>l)result.Add(new(g,l,t,r,b));}return result;
    }
    public byte LayerAlpha(int group,int x,int y)=>LayerChannel(group,3,x,y);
    public byte LayerChannel(int group,int channel,int x,int y){var b=footprints[group];return x<b.Left||x>=b.Right||y<b.Top||y>=b.Bottom?(byte)0:data[group][((y-b.Top)*b.Width+x-b.Left)*4+channel];}
    public byte CompositeChannel(int channel,int x,int y)
    {
        double alpha=0,value=0;for(int g=data.Length-1;g>=0;g--){double a=LayerAlpha(g,x,y)/255d;value=LayerChannel(g,channel,x,y)*a+value*(1-a);alpha=a+alpha*(1-a);}return channel==3?(byte)Math.Round(alpha*255):(byte)Math.Round(alpha>0?value/alpha:0);
    }
}

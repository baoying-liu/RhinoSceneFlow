namespace RhinoSceneFlow.Core;

public sealed record DepthTile(int Width,int Height,double[] Distance,byte[] Coverage);

/// <summary>Camera-axis linear depth, using owned geometry and the same billboard axes.
/// Empty rays never participate in normalization. No native GPU capture or Rhino access.</summary>
public static class DepthRenderer
{
    public static DepthTile Render(int width,int height,CameraProjection camera,PlantOccluders geometry,IReadOnlyList<PlantBillboard> plants,BillboardSettings settings,CancellationToken token=default)
    {
        if(width<1||height<1||width>1024||height>1024)throw new ArgumentException("Depth tile must be <=1024.");
        var quads=plants.Select(p=>{var a=p.Axes(camera,settings);return(P:p,R:a.Right,U:a.Up,N:a.Right.Cross(a.Up).Unit);}).ToArray();
        var distances=new double[width*height];var coverage=new byte[distances.Length];
        Parallel.For(0,height,new ParallelOptions{CancellationToken=token,MaxDegreeOfParallelism=8},y=>
        {
            for(int x=0;x<width;x++)
            {
                if((x&31)==0)token.ThrowIfCancellationRequested();double sum=0;int count=0;
                for(int s=0;s<4;s++)
                {
                    double u=(x+(s%2+.5)/2)/width,v=1-(y+(s/2+.5)/2)/height;
                    var near=camera.At(u,v,camera.Near);var delta=camera.At(u,v,camera.Far)-near;double length=delta.Length;var dir=delta.Unit;
                    double best=geometry.Distance(near,dir,length);
                    foreach(var q in quads)
                    {
                        double den=dir.Dot(q.N);if(Math.Abs(den)<1e-12)continue;
                        double d=(q.P.Anchor-near).Dot(q.N)/den;if(d<0||d>length||d>=best)continue;
                        var point=near+dir*d-q.P.Anchor;double tu=point.Dot(q.R)/q.P.Width+q.P.PivotU,tv=point.Dot(q.U)/q.P.Height+q.P.AnchorV;
                        if(tu<0||tu>1||tv<0||tv>1||q.P.Image.Sample(q.P.Mirror?1-tu:tu,tv).A<.5)continue;
                        best=d;
                    }
                    if(!double.IsFinite(best))continue;
                    sum+=-(near+dir*best-camera.Origin).Dot(camera.Back);count++;
                }
                int i=y*width+x;coverage[i]=(byte)count;distances[i]=count==0?0:sum/count;
            }
        });
        return new(width,height,distances,coverage);
    }
}

/// <summary>Two streaming passes keep the range global across tiles without a full-size depth array.</summary>
public sealed class DepthPassBuilder:IDisposable
{
    private readonly FileStream raw;
    private readonly string path;
    private readonly int width,height;
    private double minimum=double.PositiveInfinity,maximum=double.NegativeInfinity;
    public DiskPassImage Image{get;}
    public double? Minimum=>double.IsFinite(minimum)?minimum:null;
    public double? Maximum=>double.IsFinite(maximum)?maximum:null;
    public DepthPassBuilder(string staging,int width,int height)
    {
        this.width=width;this.height=height;path=Path.Combine(staging,Guid.NewGuid()+".depth");raw=new(path,FileMode.Create,FileAccess.ReadWrite,FileShare.None);raw.SetLength((long)width*height*9);
        Image=new(staging,width,height,[new("深度",new(0,0,0))],true);
    }
    public void WriteTile(int left,int top,DepthTile tile,CancellationToken token=default)
    {
        if(left<0||top<0||left+tile.Width>width||top+tile.Height>height||tile.Distance.Length!=tile.Width*tile.Height||tile.Coverage.Length!=tile.Distance.Length)throw new ArgumentException("Invalid depth tile.");
        var row=new byte[tile.Width*9];
        for(int y=0;y<tile.Height;y++)
        {
            token.ThrowIfCancellationRequested();
            for(int x=0;x<tile.Width;x++)
            {
                int i=y*tile.Width+x;double d=tile.Distance[i];byte c=tile.Coverage[i];if(c>4||c>0&&!double.IsFinite(d))throw new InvalidDataException("Invalid depth sample.");
                if(c>0){minimum=Math.Min(minimum,d);maximum=Math.Max(maximum,d);}BitConverter.TryWriteBytes(row.AsSpan(x*9,8),d);row[x*9+8]=c;
            }
            raw.Position=((long)(top+y)*width+left)*9;raw.Write(row);
        }
    }
    public void Finish(CancellationToken token=default)
    {
        var row=new byte[width*9];var rgba=new byte[width*4];raw.Position=0;
        for(int y=0;y<height;y++)
        {
            token.ThrowIfCancellationRequested();raw.ReadExactly(row);
            for(int x=0;x<width;x++)
            {
                double d=BitConverter.ToDouble(row,x*9);int covered=row[x*9+8];
                double value=covered==0?0:maximum-minimum<=1e-12?1:Math.Clamp((maximum-d)/(maximum-minimum),0,1);
                byte c=(byte)Math.Round(255*value*covered/4);rgba[x*4]=rgba[x*4+1]=rgba[x*4+2]=c;rgba[x*4+3]=255;
            }
            Image.WriteRgbaRow(y,0,rgba);
        }
    }
    public void Dispose(){raw.Dispose();Image.Dispose();if(File.Exists(path))File.Delete(path);}
}

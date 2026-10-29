namespace RhinoSceneFlow.Core;

/// <summary>Direct-sun alpha cutout shadows on non-plant mesh receivers; no rectangular billboard shadows.</summary>
public static class PlantShadows
{
    public static IPsdImage Add(RasterImage original,CameraProjection camera,PlantOccluders receivers,IReadOnlyList<PlantBillboard> plants,BillboardSettings settings,Vec3 toSun,CancellationToken token=default)
    {
        var frames=plants.Select(p=>{var a=p.Axes(camera,settings);return(P:p,R:a.Right,U:a.Up,N:a.Right.Cross(a.Up).Unit);}).ToArray();
        var alpha=new byte[original.Width*original.Height];var sun=toSun.Unit;
        Parallel.For(0,original.Height,new ParallelOptions{CancellationToken=token,MaxDegreeOfParallelism=8},y=>
        {
            for(int x=0;x<original.Width;x++)
            {
                if((x&63)==0)token.ThrowIfCancellationRequested();double total=0;
                for(int s=0;s<4;s++)
                {
                    if(original.SampleOwner(x,y,s)>=0){total+=1;continue;}
                    var near=camera.At((x+(s%2+.5)/2)/original.Width,1-(y+(s/2+.5)/2)/original.Height,camera.Near);var delta=camera.At((x+(s%2+.5)/2)/original.Width,1-(y+(s/2+.5)/2)/original.Height,camera.Far)-near;
                    double d=receivers.Distance(near,delta.Unit,delta.Length);if(!double.IsFinite(d))continue;var point=near+delta.Unit*d;double transmitted=1;
                    foreach(var frame in frames)
                    {
                        double den=sun.Dot(frame.N);if(Math.Abs(den)<1e-12)continue;double distance=(frame.P.Anchor-point).Dot(frame.N)/den;if(distance<=Math.Max(1e-8,frame.P.Height*1e-8))continue;
                        var q=point+sun*distance-frame.P.Anchor;double u=q.Dot(frame.R)/frame.P.Width+frame.P.PivotU,v=q.Dot(frame.U)/frame.P.Height+frame.P.AnchorV;
                        if(u<0||u>1||v<0||v>1)continue;transmitted*=1-frame.P.Image.Sample(frame.P.Mirror?1-u:u,v).A;
                    }
                    total+=1-transmitted;
                }
                alpha[y*original.Width+x]=(byte)Math.Clamp(Math.Round(total*255/4),0,255);
            }
        });return new Mask(original,alpha);
    }
    private sealed class Mask(RasterImage image,byte[] alpha):IPsdImage
    {
        public int Width=>image.Width;public int Height=>image.Height;public IReadOnlyList<ColorGroup> Groups=>image.Groups;
        public byte LayerAlpha(int g,int x,int y)=>alpha[y*Width+x];
        public byte CompositeChannel(int c,int x,int y)=>c==3?LayerAlpha(0,x,y):c==0?Groups[0].Color.R:c==1?Groups[0].Color.G:Groups[0].Color.B;
        public IReadOnlyList<LayerBounds> GetVisibleLayers(CancellationToken cancellation=default)
        {
            int l=Width,t=Height,r=0,b=0;for(int y=0;y<Height;y++){cancellation.ThrowIfCancellationRequested();for(int x=0;x<Width;x++)if(alpha[y*Width+x]>0){l=Math.Min(l,x);t=Math.Min(t,y);r=Math.Max(r,x+1);b=Math.Max(b,y+1);}}return r>l?[new(0,l,t,r,b)]:[];
        }
    }
}

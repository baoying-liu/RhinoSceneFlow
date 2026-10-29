using g3;
namespace RhinoSceneFlow.Core;

/// <summary>Owned non-plant geometry tree, independent of the Rhino SDK and camera-facing assets.</summary>
public sealed class PlantOccluders
{
    private readonly DMesh3 mesh=new();private readonly DMeshAABBTree3? tree;private readonly Vec3 origin;
    public PlantOccluders(IEnumerable<WorldTriangle> triangles,Vec3 origin,CancellationToken token=default)
    {
        this.origin=origin;
        foreach(var t in triangles)
        {
            token.ThrowIfCancellationRequested();var a=G(t.A-origin);var b=G(t.B-origin);var c=G(t.C-origin);
            if((b-a).Cross(c-a).LengthSquared<1e-24)continue;
            int ia=mesh.AppendVertex(a),ib=mesh.AppendVertex(b),ic=mesh.AppendVertex(c);mesh.AppendTriangle(ia,ib,ic);
        }
        if(mesh.TriangleCount>0)tree=new(mesh,true);
    }
    private static Vector3d G(Vec3 p)=>new(p.X,p.Y,p.Z);
    public double Distance(Vec3 point,Vec3 direction,double length)
    {
        if(tree==null)return double.PositiveInfinity;var ray=new Ray3d(G(point-origin),G(direction));int id=tree.FindNearestHitTriangle(ray,length);
        return id<0?double.PositiveInfinity:MeshQueries.TriangleIntersection(mesh,id,ray).RayParameter;
    }
}

public static class PlantRasterizer
{
    public static (ColorGroup[] Groups,string[] Species,int[] Map) Layout(IReadOnlyList<PlantBillboard> plants,string grouping,CameraProjection camera)
    {
        if(grouping is not ("individual" or "species" or "all"))throw new ArgumentException("植物分层：individual | species | all");
        var ordered=plants.Select((p,i)=>(p,i)).OrderBy(v=>v.p.Species,StringComparer.Ordinal).ThenByDescending(v=>(v.p.Anchor-camera.Origin).Dot(camera.Back)).ThenBy(v=>v.p.Id,StringComparer.Ordinal).ToArray();
        var keys=ordered.Select(v=>grouping=="all"?"all":grouping=="species"?v.p.Species:v.p.Id).Distinct().ToArray();
        if(keys.Length==0)keys=["empty"];
        var species=keys.Select(k=>ordered.FirstOrDefault(v=>(grouping=="all"?"all":grouping=="species"?v.p.Species:v.p.Id)==k).p?.Species??"").ToArray();
        var groups=keys.Select((k,i)=>new ColorGroup(grouping=="all"?"全部植物":grouping=="species"?species[i]:ordered.First(v=>v.p.Id==k).p.Name,new(0,0,0))).ToArray();
        if(plants.Count==0)groups=[new("植物",new(0,0,0))];
        var map=plants.Select(p=>Array.IndexOf(keys,grouping=="all"?"all":grouping=="species"?p.Species:p.Id)).ToArray();return(groups,species,map);
    }
    private sealed record Quad(PlantBillboard Plant,Vec3 Right,Vec3 Up,Vec3 Normal,int Left,int Top,int RightPixel,int Bottom,int Group);
    private readonly record struct Hit(double Depth,int Plant,double R,double G,double B,double A);
    public static IPsdImage Render(int width,int height,CameraProjection camera,IReadOnlyList<PlantBillboard> plants,BillboardSettings settings,PlantOccluders occluders,string grouping,CancellationToken token=default)
    {
        if(width<1||height<1||width>1024||height>1024)throw new ArgumentException("Plant tile must be <=1024.");
        var layout=Layout(plants,grouping,camera);var quads=new List<Quad>();var boxes=layout.Groups.Select((_,i)=>new LayerBounds(i,width,height,0,0)).ToArray();
        for(int i=0;i<plants.Count;i++)
        {
            var p=plants[i];var axes=p.Axes(camera,settings);var corners=new[]{p.Anchor-axes.Right*(p.Width*p.PivotU)-axes.Up*(p.Height*p.AnchorV),p.Anchor+axes.Right*(p.Width*(1-p.PivotU))-axes.Up*(p.Height*p.AnchorV),p.Anchor+axes.Right*(p.Width*(1-p.PivotU))+axes.Up*(p.Height*(1-p.AnchorV)),p.Anchor-axes.Right*(p.Width*p.PivotU)+axes.Up*(p.Height*(1-p.AnchorV))}.Select(camera.Project).ToArray();
            if(corners.All(c=>c.W<=0)||corners.All(c=>c.Z<0)||corners.All(c=>c.Z>c.W))continue;
            bool crosses=corners.Any(c=>c.W<=0||c.Z<0);
            var xs=corners.Where(c=>c.W>0).Select(c=>(c.X/c.W+1)*width/2).ToArray();var ys=corners.Where(c=>c.W>0).Select(c=>(1-c.Y/c.W)*height/2).ToArray();
            int l=crosses?0:(int)Math.Clamp(Math.Floor(xs.Min())-1,0,width),r=crosses?width:(int)Math.Clamp(Math.Ceiling(xs.Max())+1,0,width);
            int t=crosses?0:(int)Math.Clamp(Math.Floor(ys.Min())-1,0,height),b=crosses?height:(int)Math.Clamp(Math.Ceiling(ys.Max())+1,0,height);
            if(r<=l||b<=t)continue;
            int g=layout.Map[i];var box=boxes[g];boxes[g]=new(g,Math.Min(box.Left,l),Math.Min(box.Top,t),Math.Max(box.Right,r),Math.Max(box.Bottom,b));
            quads.Add(new(p,axes.Right,axes.Up,axes.Right.Cross(axes.Up).Unit,l,t,r,b,g));
        }
        // Crop per group; no width*height*plantCount dense allocation.
        long bytes=boxes.Sum(b=>(long)Math.Max(0,b.Width)*Math.Max(0,b.Height)*4);
        if(bytes>128L*1024*1024)throw new InvalidOperationException("单个植物渲染分块超过 128 MiB；请改为按种／全部合并，或减少当前视图中的重叠植物。");
        var pixels=boxes.Select(b=>new byte[Math.Max(0,b.Width)*Math.Max(0,b.Height)*4]).ToArray();var composite=new byte[width*height*4];
        Parallel.For(0,height,new ParallelOptions{CancellationToken=token,MaxDegreeOfParallelism=8},y=>
        {
            var candidates=quads.Where(q=>y>=q.Top&&y<q.Bottom).ToArray();var hits=new List<Hit>();var accum=new double[layout.Groups.Length*4];
            for(int x=0;x<width;x++)
            {
                if((x&63)==0)token.ThrowIfCancellationRequested();Array.Clear(accum);
                for(int s=0;s<4;s++)
                {
                    double u=(x+(s%2+.5)/2)/width,v=1-(y+(s/2+.5)/2)/height;var near=camera.At(u,v,camera.Near);var delta=camera.At(u,v,camera.Far)-near;double max=delta.Length;var dir=delta.Unit;
                    double blocked=occluders.Distance(near,dir,max);hits.Clear();
                    for(int i=0;i<candidates.Length;i++)
                    {
                        var q=candidates[i];if(x<q.Left||x>=q.RightPixel)continue;double den=dir.Dot(q.Normal);if(Math.Abs(den)<1e-12)continue;
                        double d=(q.Plant.Anchor-near).Dot(q.Normal)/den;if(d<0||d>max||d>blocked+1e-8)continue;
                        var p=near+dir*d-q.Plant.Anchor;double tu=p.Dot(q.Right)/q.Plant.Width+q.Plant.PivotU,tv=p.Dot(q.Up)/q.Plant.Height+q.Plant.AnchorV;
                        if(tu<0||tu>1||tv<0||tv>1)continue;var color=q.Plant.Image.Sample(q.Plant.Mirror?1-tu:tu,tv);if(color.A<=0)continue;
                        hits.Add(new(d,i,color.R,color.G,color.B,color.A));
                    }
                    if(grouping!="individual")hits.Sort((a,b)=>{int c=a.Depth.CompareTo(b.Depth);return c!=0?c:string.CompareOrdinal(candidates[a.Plant].Plant.Id,candidates[b.Plant].Plant.Id);});
                    double transmission=1;
                    foreach(var hit in hits)
                    {
                        int g=candidates[hit.Plant].Group;double a=hit.A*(grouping=="individual"?1:transmission)/4;
                        accum[g*4]+=hit.R*a;accum[g*4+1]+=hit.G*a;accum[g*4+2]+=hit.B*a;accum[g*4+3]+=a;
                        if(grouping!="individual")transmission*=1-hit.A;
                    }
                }
                double above=0;
                for(int g=0;g<boxes.Length;g++)
                {
                    var box=boxes[g];if(x<box.Left||x>=box.Right||y<box.Top||y>=box.Bottom)continue;
                    double a=accum[g*4+3];if(a<=0)continue;int p=((y-box.Top)*box.Width+x-box.Left)*4;
                    for(int c=0;c<3;c++)pixels[g][p+c]=Byte(accum[g*4+c]/a);
                    pixels[g][p+3]=Byte(grouping=="individual"?a:a/Math.Max(1e-12,1-above));above+=a;
                }
                double ca=0;var rgb=new double[3];
                for(int g=boxes.Length-1;g>=0;g--)
                {
                    var box=boxes[g];if(x<box.Left||x>=box.Right||y<box.Top||y>=box.Bottom)continue;int p=((y-box.Top)*box.Width+x-box.Left)*4;double a=pixels[g][p+3]/255.0;
                    for(int c=0;c<3;c++)rgb[c]=pixels[g][p+c]/255.0*a+rgb[c]*(1-a);ca=a+ca*(1-a);
                }
                int cp=(y*width+x)*4;for(int c=0;c<3;c++)composite[cp+c]=ca>0?Byte(rgb[c]/ca):(byte)0;composite[cp+3]=Byte(ca);
            }
        });
        return new PlantImage(width,height,layout.Groups,boxes,pixels,composite);
    }
    private static byte Byte(double v)=>(byte)Math.Clamp(Math.Round(v*255),0,255);
    private sealed class PlantImage(int w,int h,ColorGroup[] groups,LayerBounds[] boxes,byte[][] pixels,byte[] composite):IPsdImage
    {
        public int Width=>w;public int Height=>h;public IReadOnlyList<ColorGroup> Groups=>groups;
        public byte LayerAlpha(int g,int x,int y)=>LayerChannel(g,3,x,y);
        public byte LayerChannel(int g,int c,int x,int y){var b=boxes[g];return x<b.Left||x>=b.Right||y<b.Top||y>=b.Bottom?(byte)0:pixels[g][((y-b.Top)*b.Width+x-b.Left)*4+c];}
        public byte CompositeChannel(int c,int x,int y)=>composite[(y*w+x)*4+c];
        public IReadOnlyList<LayerBounds> GetVisibleLayers(CancellationToken cancellation=default)=>boxes.Where(b=>b.Width>0&&b.Height>0&&pixels[b.Group].Where((v,i)=>i%4==3&&v>0).Any()).ToArray();
    }
}

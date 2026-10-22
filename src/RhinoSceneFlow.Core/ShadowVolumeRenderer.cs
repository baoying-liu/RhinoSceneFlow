namespace RhinoSceneFlow.Core;

/// <summary>
/// Software z-fail shadow volumes. Each opaque, two-sided triangle generates a closed
/// prism; signed shared side walls cancel exactly. No topology welding or shading-normal
/// displacement is required. Volumes are not clipped at the camera far plane: their
/// closing caps must participate even when outside the visible scene depth range.
/// </summary>
public static class ShadowVolumeRenderer
{
    public static RasterImage Render(int width, int height, CameraProjection camera,
        IReadOnlyList<WorldTriangle> triangles, ShadowSettings settings, CancellationToken cancellation = default,
        Func<int,int,bool>? refineSurface = null)
    {
        if (width < 1 || height < 1 || width > 8192 || height > 8192 || (long)width * height > 8_000_000)
            throw new ArgumentOutOfRangeException(nameof(width));
        if (!(settings.Bias > 0) || !double.IsFinite(settings.Bias)) throw new ArgumentException("Bias must be finite and positive.");
        if (!(settings.Opacity > 0 && settings.Opacity <= 1)) throw new ArgumentException("Opacity must be in (0,1].");
        var sun = settings.ToSun.Unit;
        var origin = camera.Origin;
        camera = camera with { Origin = new(0, 0, 0) };
        var scene = triangles.Select(t => t with { A=t.A-origin, B=t.B-origin, C=t.C-origin })
            .Where(t => Finite(t.A) && Finite(t.B) && Finite(t.C) && (t.B-t.A).Cross(t.C-t.A).Length > 1e-14).ToArray();
        int sw = width*2, sh = height*2, size = checked(sw*sh);
        var depth = new double[size]; Array.Fill(depth, double.PositiveInfinity);
        var receiver = new int[size]; Array.Fill(receiver, -1);
        var stencil = new int[size];
        var owners = new int[size]; Array.Fill(owners, -1);
        var evaluated = refineSurface is null ? null : new byte[size];
        if (scene.Length == 0) return new(width,height,[new("Shadow",settings.Color)],owners,settings.Opacity);
        double Distance(double z) => camera.Parallel ? camera.Near+z*(camera.Far-camera.Near) :
            camera.Far*camera.Near/(camera.Far-z*(camera.Far-camera.Near));
        for (int id=0; id<scene.Length; id++)
        {
            var t=scene[id]; int current=id;
            Raster(camera.Project(t.A),camera.Project(t.B),camera.Project(t.C),true,sw,sh,
                (index,z,_) => { if (z < depth[index]) { depth[index]=z; receiver[index]=current; } },cancellation);
        }
        // A cap past the minimum scene coordinate along the sunlight axis cannot
        // truncate a shadow on any scene receiver. Include off-camera casters too.
        double min=double.PositiveInfinity,max=double.NegativeInfinity;
        foreach(var t in scene) foreach(var p in new[]{t.A,t.B,t.C})
        { double d=p.Dot(sun); min=Math.Min(min,d); max=Math.Max(max,d); }
        var extrusion = sun * -(max-min+Math.Max(1,(max-min)*.01));
        var edges = new Dictionary<(Vec3,Vec3),int>();
        void Edge(Vec3 a,Vec3 b)
        {
            bool forward=Compare(a,b)<0;
            var key=forward?(a,b):(b,a);
            edges[key]=edges.GetValueOrDefault(key)+(forward?1:-1);
        }
        // Compare in camera distance, so bias remains in model units. Never apply
        // smooth normals to occlusion. Signed counts use full integers, not 8-bit wrap.
        void VolumeFace(Vec3 a,Vec3 b,Vec3 c,int multiplicity=1) =>
            Raster(camera.Project(a),camera.Project(b),camera.Project(c),false,sw,sh,(index,z,sign) =>
            {
                if (receiver[index]>=0 && Distance(z)>=Distance(depth[index])-settings.Bias)
                    stencil[index]+=sign*multiplicity;
            },cancellation);
        foreach (var t in scene)
        {
            cancellation.ThrowIfCancellationRequested();
            var a=t.A; var b=t.B; var c=t.C;
            double facing=(b-a).Cross(c-a).Dot(sun);
            if (Math.Abs(facing)<1e-14*(b-a).Length*(c-a).Length) continue;
            if (facing<0) (b,c)=(c,b);
            VolumeFace(a,b,c);
            VolumeFace(a+extrusion,c+extrusion,b+extrusion);
            Edge(a,b); Edge(b,c); Edge(c,a);
        }
        foreach(var (edge,count) in edges)
        {
            if(count==0) continue;
            var (a,b)=edge;
            VolumeFace(b,a,a+extrusion,count);
            VolumeFace(b,a+extrusion,b+extrusion,count);
        }
        for(int y=0;y<sh;y++)
        {
            cancellation.ThrowIfCancellationRequested();
            for(int x=0;x<sw;x++)
            {
                int index=y*sw+x,id=receiver[index]; if(id<0) continue;
                var t=scene[id];
                var point=camera.At((x+.5)/sw,1-(y+.5)/sh,Distance(depth[index]));
                var view=camera.Parallel ? camera.Back : camera.Origin-point;
                var geometric=(t.B-t.A).Cross(t.C-t.A).Unit;
                if(geometric.Dot(view)<0) geometric=geometric*-1;
                var normal=geometric;
                if(t.NA.HasValue && t.NB.HasValue && t.NC.HasValue)
                {
                    var u=t.B-t.A; var v=t.C-t.A; var p=point-t.A;
                    double uu=u.Dot(u),uv=u.Dot(v),vv=v.Dot(v),pu=p.Dot(u),pv=p.Dot(v),den=uu*vv-uv*uv;
                    if(den>0)
                    {
                        double wb=(vv*pu-uv*pv)/den,wc=(uu*pv-uv*pu)/den;
                        var smooth=t.NA.Value*(1-wb-wc)+t.NB.Value*wb+t.NC.Value*wc;
                        if(smooth.Length>1e-14) normal=smooth.Unit;
                        if(normal.Dot(geometric)<0) normal=normal*-1;
                    }
                }
                // Backlighting is controlled separately. Geometric backfaces are not
                // counted as cast shadows from their own faceted approximation.
                bool form=settings.IncludeFormShading && normal.Dot(sun)<=1e-10;
                bool shadow=form || (geometric.Dot(sun)>1e-10 && stencil[index]!=0);
                if(refineSurface is not null && t.NA.HasValue && t.NB.HasValue && t.NC.HasValue)
                {
                    Vec3 Orient(Vec3 n) => n.Dot(geometric)<0 ? n*-1 : n;
                    var na=Orient(t.NA.Value);var nb=Orient(t.NB.Value);var nc=Orient(t.NC.Value);
                    double variation=Math.Max((na-nb).Length,Math.Max((na-nc).Length,(nb-nc).Length));
                    double uncertainty=2*Math.Max(Math.Abs(geometric.Dot(sun)-normal.Dot(sun)),variation)+1e-6;
                    // Re-evaluate actual geometry, not the image, where faceting can
                    // change terminator classification or create false self-occlusion.
                    if(variation>1e-6 && (shadow || Math.Abs(normal.Dot(sun))<=uncertainty))
                    { shadow=refineSurface(x,y);evaluated![index]=1; }
                }
                if(shadow) owners[index]=0;
            }
        }
        if(refineSurface is not null)
        {
            // A mesh silhouette can also move a shadow between different receivers,
            // including a flat wall. Select both sides of coverage boundaries, then
            // classify their 3D rays against the source geometry. Selection is frozen
            // before any results change; this is not dilation of the output image.
            for(int y=0;y<sh;y++)
            {
                cancellation.ThrowIfCancellationRequested();
                for(int x=0;x<sw;x++)
                {
                    int i=y*sw+x;if(evaluated![i]!=0)continue;
                    for(int dy=-1;dy<=1 && evaluated[i]==0;dy++)for(int dx=-1;dx<=1;dx++)
                        if(x+dx>=0&&x+dx<sw&&y+dy>=0&&y+dy<sh&&owners[i]!=owners[(y+dy)*sw+x+dx])
                        {evaluated[i]=2;break;}
                }
            }
            for(int y=0;y<sh;y++)
            {
                cancellation.ThrowIfCancellationRequested();
                for(int x=0;x<sw;x++)if(evaluated![y*sw+x]==2)
                    owners[y*sw+x]=refineSurface(x,y)?0:-1;
            }
        }
        return new(width,height,[new("Shadow",settings.Color)],owners,settings.Opacity);
    }

    private static bool Finite(Vec3 v) => double.IsFinite(v.X)&&double.IsFinite(v.Y)&&double.IsFinite(v.Z);
    private static int Compare(Vec3 a,Vec3 b)
    { int c=a.X.CompareTo(b.X); if(c!=0)return c; c=a.Y.CompareTo(b.Y); return c!=0?c:a.Z.CompareTo(b.Z); }
    private static double Plane(ClipVertex v,int plane) => plane switch
    { 0=>v.X+v.W,1=>v.W-v.X,2=>v.Y+v.W,3=>v.W-v.Y,4=>v.Z,_=>v.W-v.Z };
    private readonly record struct Screen(double X,double Y,double Z);
    private static double Cross(Screen a,Screen b,double x,double y) => (b.X-a.X)*(y-a.Y)-(b.Y-a.Y)*(x-a.X);
    private static bool TopLeft(Screen a,Screen b) => b.Y<a.Y || (b.Y==a.Y && b.X>a.X);

    private static void Raster(ClipVertex a,ClipVertex b,ClipVertex c,bool clipFar,int width,int height,
        Action<int,double,int> fragment,CancellationToken cancellation)
    {
        var polygon=new List<ClipVertex>{a,b,c};
        for(int plane=0;plane<(clipFar?6:5)&&polygon.Count>0;plane++)
        {
            var output=new List<ClipVertex>(polygon.Count+1);
            var previous=polygon[^1]; double pd=Plane(previous,plane);
            foreach(var current in polygon)
            {
                double cd=Plane(current,plane);
                if((pd>=0)!=(cd>=0)) output.Add(ClipVertex.Lerp(previous,current,pd/(pd-cd)));
                if(cd>=0) output.Add(current);
                previous=current; pd=cd;
            }
            polygon=output;
        }
        Screen Project(ClipVertex p) => new((p.X/p.W+1)*width*.5,(1-p.Y/p.W)*height*.5,p.Z/p.W);
        for(int i=1;i+1<polygon.Count;i++)
        {
            if(polygon[0].W<=0 || polygon[i].W<=0 || polygon[i+1].W<=0)continue;
            var op=Project(polygon[0]); var oq=Project(polygon[i]); var or=Project(polygon[i+1]);
            Screen Snap(Screen v) => v with { X=Math.Round(v.X*256)/256,Y=Math.Round(v.Y*256)/256 };
            var p=Snap(op); var q=Snap(oq); var r=Snap(or);
            double originalArea=Cross(op,oq,or.X,or.Y); if(Math.Abs(originalArea)<1e-15)continue;
            double area=Cross(p,q,r.X,r.Y); if(Math.Abs(area)<1e-12)continue;
            int sign=area>0?1:-1;
            if(area<0){(q,r)=(r,q);area=-area;}
            int x0=Math.Max(0,(int)Math.Ceiling(Math.Min(p.X,Math.Min(q.X,r.X))-.5));
            int x1=Math.Min(width-1,(int)Math.Floor(Math.Max(p.X,Math.Max(q.X,r.X))-.5));
            int y0=Math.Max(0,(int)Math.Ceiling(Math.Min(p.Y,Math.Min(q.Y,r.Y))-.5));
            int y1=Math.Min(height-1,(int)Math.Floor(Math.Max(p.Y,Math.Max(q.Y,r.Y))-.5));
            bool tl0=TopLeft(q,r),tl1=TopLeft(r,p),tl2=TopLeft(p,q);
            for(int y=y0;y<=y1;y++)
            {
                cancellation.ThrowIfCancellationRequested();
                for(int x=x0;x<=x1;x++)
                {
                    double w0=Cross(q,r,x+.5,y+.5),w1=Cross(r,p,x+.5,y+.5),w2=Cross(p,q,x+.5,y+.5);
                    if(w0<0 || (w0==0&&!tl0) || w1<0 || (w1==0&&!tl1) || w2<0 || (w2==0&&!tl2))continue;
                    // Coverage uses a fixed subpixel grid to make opposite shared edges
                    // watertight. Depth uses the original plane, avoiding bias from snapping.
                    double z=(Cross(oq,or,x+.5,y+.5)*op.Z+Cross(or,op,x+.5,y+.5)*oq.Z+Cross(op,oq,x+.5,y+.5)*or.Z)/originalArea;
                    fragment(y*width+x,z,sign);
                }
            }
        }
    }
}

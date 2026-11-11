namespace RhinoSceneFlow.Core;

public readonly record struct Uv(double U,double V)
{
    public static Uv Lerp(Uv a,Uv b,double t)=>new(a.U+(b.U-a.U)*t,a.V+(b.V-a.V)*t);
}
public sealed record PixelTexture(int Width,int Height,byte[] Rgb,bool RepeatU=true,bool RepeatV=true)
{
    public Rgb Sample(Uv uv)
    {
        if(!double.IsFinite(uv.U)||!double.IsFinite(uv.V))throw new InvalidDataException("Invalid texture coordinates.");
        double u=RepeatU?uv.U-Math.Floor(uv.U):Math.Clamp(uv.U,0,1),v=RepeatV?uv.V-Math.Floor(uv.V):Math.Clamp(uv.V,0,1);
        double x=u*Width-.5,y=(1-v)*Height-.5;int x0=(int)Math.Floor(x),y0=(int)Math.Floor(y);double fx=x-x0,fy=y-y0;
        int Wrap(int i,int size,bool repeat)=>repeat?(i%size+size)%size:Math.Clamp(i,0,size-1);
        byte C(int c)
        {
            double P(int px,int py)=>Rgb[(Wrap(py,Height,RepeatV)*Width+Wrap(px,Width,RepeatU))*3+c];
            return (byte)Math.Clamp(Math.Round((P(x0,y0)*(1-fx)+P(x0+1,y0)*fx)*(1-fy)+(P(x0,y0+1)*(1-fx)+P(x0+1,y0+1)*fx)*fy),0,255);
        }
        return new(C(0),C(1),C(2));
    }
}
public sealed record TextureSurface(string MaterialKey,string MaterialName,Rgb Color,PixelTexture? Texture,bool Modulate=true,double TextureAmount=1,Rgb? Representative=null);
public sealed record TextureObject(string Key,string Name,int Material);
public readonly record struct TextureTriangle(Vec3 A,Vec3 B,Vec3 C,Uv UA,Uv UB,Uv UC,int Object,bool UseTexture=true);

/// <summary>Owned albedo and owner samples share one depth decision. Grouping never changes visibility.</summary>
public static class TexturedRasterizer
{
    private readonly record struct Vertex(ClipVertex P,Uv U)
    {public static Vertex Lerp(Vertex a,Vertex b,double t)=>new(ClipVertex.Lerp(a.P,b.P,t),Uv.Lerp(a.U,b.U,t));}
    public static TextureSamples Render(int width,int height,CameraProjection camera,IReadOnlyList<TextureSurface> surfaces,IReadOnlyList<TextureObject> objects,IEnumerable<TextureTriangle> triangles,CancellationToken token=default,bool flatColor=false)
    {
        if(width<1||height<1||(long)width*height>2_000_000)throw new ArgumentException("Texture render tile too large.");
        int sw=width*2,sh=height*2;var owners=new int[sw*sh];Array.Fill(owners,-1);var colors=new uint[owners.Length];var depth=new double[owners.Length];Array.Fill(depth,double.PositiveInfinity);
        foreach(var t in triangles)
        {
            token.ThrowIfCancellationRequested();var poly=new List<Vertex>{new(camera.Project(t.A),t.UA),new(camera.Project(t.B),t.UB),new(camera.Project(t.C),t.UC)};
            if(poly.Any(v=>!v.P.IsFinite))continue;
            for(int p=0;p<6&&poly.Count>0;p++)
            {
                double D(Vertex v)=>p switch{0=>v.P.X+v.P.W,1=>v.P.W-v.P.X,2=>v.P.Y+v.P.W,3=>v.P.W-v.P.Y,4=>v.P.Z,_=>v.P.W-v.P.Z};
                var output=new List<Vertex>();var prev=poly[^1];double pd=D(prev);
                foreach(var curr in poly){double cd=D(curr);if((pd>=0)!=(cd>=0))output.Add(Vertex.Lerp(prev,curr,pd/(pd-cd)));if(cd>=0)output.Add(curr);prev=curr;pd=cd;}poly=output;
            }
            for(int i=1;i+1<poly.Count;i++)Draw(poly[0],poly[i],poly[i+1],t);
        }
        return new(width,height,owners,colors,objects,surfaces);

        void Draw(Vertex a,Vertex b,Vertex c,TextureTriangle triangle)
        {
            if(a.P.W<=0||b.P.W<=0||c.P.W<=0)return;
            (double X,double Y,double Z) Screen(Vertex v)=>((v.P.X/v.P.W+1)*sw/2,(1-v.P.Y/v.P.W)*sh/2,v.P.Z/v.P.W);
            var sa=Screen(a);var sb=Screen(b);var sc=Screen(c);
            double Edge((double X,double Y,double Z) x,(double X,double Y,double Z) y,double px,double py)=>(y.X-x.X)*(py-x.Y)-(y.Y-x.Y)*(px-x.X);
            double area=Edge(sa,sb,sc.X,sc.Y);if(Math.Abs(area)<1e-12)return;
            if(area<0){(sb,sc)=(sc,sb);(b,c)=(c,b);area=-area;}
            int x0=Math.Max(0,(int)Math.Floor(Math.Min(sa.X,Math.Min(sb.X,sc.X)))),x1=Math.Min(sw-1,(int)Math.Ceiling(Math.Max(sa.X,Math.Max(sb.X,sc.X))));
            int y0=Math.Max(0,(int)Math.Floor(Math.Min(sa.Y,Math.Min(sb.Y,sc.Y)))),y1=Math.Min(sh-1,(int)Math.Ceiling(Math.Max(sa.Y,Math.Max(sb.Y,sc.Y))));
            var surface=surfaces[objects[triangle.Object].Material];
            for(int y=y0;y<=y1;y++)
            {
                token.ThrowIfCancellationRequested();
                for(int x=x0;x<=x1;x++)
                {
                    double wa=Edge(sb,sc,x+.5,y+.5),wb=Edge(sc,sa,x+.5,y+.5),wc=Edge(sa,sb,x+.5,y+.5);
                    if(wa< -1e-9||wb< -1e-9||wc< -1e-9)continue;
                    double z=(wa*sa.Z+wb*sb.Z+wc*sc.Z)/area;int index=y*sw+x;
                    if(z>depth[index]+1e-12||(Math.Abs(z-depth[index])<=1e-12&&owners[index]>=0&&triangle.Object>=owners[index]))continue;
                    double q=wa/a.P.W+wb/b.P.W+wc/c.P.W;
                    var uv=new Uv((wa*a.U.U/a.P.W+wb*b.U.U/b.P.W+wc*c.U.U/c.P.W)/q,(wa*a.U.V/a.P.W+wb*b.U.V/b.P.W+wc*c.U.V/c.P.W)/q);
                    bool textured=!flatColor&&triangle.UseTexture&&surface.Texture!=null;
                    var color=flatColor?surface.Representative??surface.Color:textured?surface.Texture!.Sample(uv):surface.Color;
                    byte Mul(byte v,byte m)=>(byte)((v*m+127)/255);
                    byte Mix(byte value,byte fallback)=>(byte)Math.Clamp(Math.Round(value*surface.TextureAmount+fallback*(1-surface.TextureAmount)),0,255);
                    if(textured)color=surface.Modulate?new(Mul(color.R,surface.Color.R),Mul(color.G,surface.Color.G),Mul(color.B,surface.Color.B)):
                        new(Mix(color.R,surface.Color.R),Mix(color.G,surface.Color.G),Mix(color.B,surface.Color.B));
                    colors[index]=(uint)(color.R<<16|color.G<<8|color.B);owners[index]=triangle.Object;depth[index]=z;
                }
            }
        }
    }
}

public sealed class TextureSamples(int width,int height,int[] owners,uint[] colors,IReadOnlyList<TextureObject> objects,IReadOnlyList<TextureSurface> surfaces)
{
    public IPsdImage Grouped(string grouping)
    {
        if(grouping is not ("material" or "object" or "all"))throw new ArgumentException("Invalid texture grouping.");
        var keys=objects.Select((o,i)=>grouping=="all"?"all":grouping=="object"?o.Key:surfaces[o.Material].MaterialKey).ToArray();
        var unique=keys.Distinct().Order(StringComparer.Ordinal).ToArray();if(unique.Length==0)unique=["empty"];
        var index=unique.Select((key,i)=>(key,i)).ToDictionary(p=>p.key,p=>p.i);
        var map=keys.Select(k=>index[k]).ToArray();
        var groups=unique.Select(key=>{int i=Array.IndexOf(keys,key);return new ColorGroup(grouping=="all"?"全部物件":i<0?"未指定材质":grouping=="object"?objects[i].Name+" · "+surfaces[objects[i].Material].MaterialName:surfaces[objects[i].Material].MaterialName,new(0,0,0));}).ToArray();
        return new SampleImage(width,height,owners,colors,map,groups);
    }
    private sealed class SampleImage(int width,int height,int[] owners,uint[] colors,int[] map,ColorGroup[] groups) : IPsdImage
    {
        public int Width=>width;public int Height=>height;public IReadOnlyList<ColorGroup> Groups=>groups;
        private LayerBounds[]? bounds;
        private int At(int x,int y,int s)=>(y*2+s/2)*width*2+x*2+s%2;
        public IReadOnlyList<LayerBounds> GetVisibleLayers(CancellationToken cancellation=default)
        {
            if(bounds!=null)return bounds;var b=Enumerable.Range(0,groups.Length).Select(g=>new LayerBounds(g,width,height,0,0)).ToArray();
            for(int y=0;y<height;y++){cancellation.ThrowIfCancellationRequested();for(int x=0;x<width;x++)for(int s=0;s<4;s++){int o=owners[At(x,y,s)];if(o<0)continue;int g=map[o];var old=b[g];b[g]=new(g,Math.Min(old.Left,x),Math.Min(old.Top,y),Math.Max(old.Right,x+1),Math.Max(old.Bottom,y+1));}}
            return bounds=b.Where(v=>v.Right>v.Left).ToArray();
        }
        public byte LayerChannel(int group,int channel,int x,int y)
        {
            int own=0,above=0,sum=0;
            for(int s=0;s<4;s++){int i=At(x,y,s),o=owners[i];if(o<0)continue;int g=map[o];if(g==group){own++;if(channel<3)sum+=(byte)(colors[i]>>(16-channel*8));}else if(g<group)above++;}
            return channel==3?(byte)(own==0?0:Math.Round(255.0*own/(4-above))):(byte)(own==0?0:Math.Round((double)sum/own));
        }
        public byte LayerAlpha(int group,int x,int y)=>LayerChannel(group,3,x,y);
        public byte CompositeChannel(int channel,int x,int y)
        {
            int covered=0,sum=0;for(int s=0;s<4;s++){int i=At(x,y,s);if(owners[i]<0)continue;covered++;if(channel<3)sum+=(byte)(colors[i]>>(16-channel*8));}
            return channel==3?(byte)Math.Round(covered*255.0/4):(byte)(covered==0?0:Math.Round((double)sum/covered));
        }
    }
}

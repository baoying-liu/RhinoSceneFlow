namespace RhinoSceneFlow.Core;

public sealed class PlantIdentity
{
    public string ScientificName {get;set;}="";
    public string Family {get;set;}="";
    public string Genus {get;set;}="";
    public string Cultivar {get;set;}="";
    public Dictionary<string,string> Names {get;set;}=[];
    public string[] Sources {get;set;}=[];
    public string Evidence {get;set;}="";
    public DateTime VerifiedUtc {get;set;}
    public bool EstimatedSize {get;set;}=true;
    public double SpacingMeters {get;set;}=1;
    public string SpacingEvidence {get;set;}="旧素材默认 1 m，请按种植需求调整。";
    public double AnchorU {get;set;}=.5;
    public double AnchorV {get;set;}=0;
    public void Validate()
    {
        if(Names.Count>8||Names.Any(p=>p.Key.Length>16||p.Value==null||p.Value.Length>100))throw new ArgumentException("植物本地化名称无效。");
        if(!double.IsFinite(SpacingMeters)||SpacingMeters<=0||SpacingMeters>1000||string.IsNullOrWhiteSpace(ScientificName)||ScientificName.Length>200||string.IsNullOrWhiteSpace(Family)||string.IsNullOrWhiteSpace(Genus)||Sources.Length==0||Sources.Any(s=>!Uri.TryCreate(s,UriKind.Absolute,out var u)||u.Scheme!="https")||!double.IsFinite(AnchorU)||!double.IsFinite(AnchorV)||AnchorU<0||AnchorU>1||AnchorV<0||AnchorV>1)throw new ArgumentException("植物需要学名、科属、来源和有效基部锚点。");
    }
}
public sealed class BillboardSettings
{
    public string Mode {get;set;}="auto";
    public double Angle {get;set;}=60;
    public double Transition {get;set;}=5;
    public void Validate(){if(Mode is not ("auto" or "z" or "free")||!double.IsFinite(Angle)||Angle<10||Angle>85||!double.IsFinite(Transition)||Transition<1||Transition>15)throw new ArgumentException("朝向模式或切换角度无效。");}
}
public sealed record PlantBillboard(string Id,string Species,string Name,Vec3 Anchor,double Width,double Height,double AnchorU,double AnchorV,bool Mirror,RgbaTexture Image)
{
    public double PivotU=>Mirror?1-AnchorU:AnchorU;
    public (Vec3 Right,Vec3 Up) Axes(CameraProjection camera,BillboardSettings settings)
    {
        settings.Validate();var offset=camera.Origin-Anchor;var back=camera.Parallel||offset.Length<1e-9?camera.Back:offset.Unit;
        var flat=new Vec3(back.X,back.Y,0);var right=flat.Length>1e-9?new Vec3(0,0,1).Cross(flat).Unit:camera.Right;
        var up=new Vec3(0,0,1);
        double elevation=Math.Asin(Math.Clamp(Math.Abs(back.Z),0,1))*180/Math.PI;
        double t=settings.Mode=="free"?1:settings.Mode=="z"?0:Math.Clamp((elevation-settings.Angle+settings.Transition)/(2*settings.Transition),0,1);
        // Smooth, deterministic transition: preview/export agree and angle-boundary jitter cannot toggle modes.
        t=t*t*(3-2*t);var blended=right*(1-t)+camera.Right*t;right=blended.Length>1e-8?blended.Unit:camera.Right;up=(up*(1-t)+camera.Up*t);up=up-right*up.Dot(right);
        if(up.Length<1e-8)up=camera.Up-right*camera.Up.Dot(right);up=up.Unit;
        return(right,up);
    }
}
public sealed record RgbaTexture(int Width,int Height,byte[] Pixels)
{
    public (double R,double G,double B,double A) Sample(double u,double v)
    {
        double x=Math.Clamp(u*Width-.5,0,Width-1),y=Math.Clamp((1-v)*Height-.5,0,Height-1);int ix=(int)x,iy=(int)y;double fx=x-ix,fy=y-iy;
        double a=0,r=0,g=0,b=0;
        for(int j=0;j<2;j++)for(int i=0;i<2;i++)
        {
            int p=(Math.Min(iy+j,Height-1)*Width+Math.Min(ix+i,Width-1))*4;double w=(i==0?1-fx:fx)*(j==0?1-fy:fy),alpha=Pixels[p+3]/255.0*w;
            a+=alpha;r+=Pixels[p]/255.0*alpha;g+=Pixels[p+1]/255.0*alpha;b+=Pixels[p+2]/255.0*alpha;
        }
        return(a>0?r/a:0,a>0?g/a:0,a>0?b/a:0,a);
    }
}

/// <summary>Nested scientific-name folders over a sparse plant pass.</summary>
public sealed class PlantHierarchy(IPsdImage image,string grouping,IReadOnlyList<string> species):IPsdImage,IPsdHierarchy
{
    public int Width=>image.Width;public int Height=>image.Height;public IReadOnlyList<ColorGroup> Groups=>image.Groups;
    public IReadOnlyList<LayerBounds> GetVisibleLayers(CancellationToken cancellation=default)=>image.GetVisibleLayers(cancellation);
    public byte LayerAlpha(int g,int x,int y)=>image.LayerAlpha(g,x,y);
    public byte LayerChannel(int g,int c,int x,int y)=>image.LayerChannel(g,c,x,y);
    public byte CompositeChannel(int c,int x,int y)=>image.CompositeChannel(c,x,y);
    public void ReadLayerRow(int g,int c,int y,int l,Span<byte> row)=>image.ReadLayerRow(g,c,y,l,row);
    public void ReadCompositeRow(int c,int y,Span<byte> row)=>image.ReadCompositeRow(c,y,row);
    public IReadOnlyList<PsdRecord> Records(CancellationToken cancellation=default)
    {
        var result=new List<PsdRecord>();var bounds=image.GetVisibleLayers(cancellation);
        string? previous=null;
        foreach(var b in bounds)
        {
            if(grouping=="individual"&&previous!=species[b.Group])
            {
                if(previous!=null)result.Add(new(new(-1,0,0,0,0),"</Plant species>",Section:3));
                previous=species[b.Group];result.Add(new(new(-1,0,0,0,0),previous,Section:1));
            }
            result.Add(new(b,image.Groups[b.Group].Name));
        }
        if(previous!=null)result.Add(new(new(-1,0,0,0,0),"</Plant species>",Section:3));
        return result;
    }
}

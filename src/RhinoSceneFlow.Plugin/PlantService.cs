using System.Drawing.Imaging;
using System.Runtime.InteropServices;
using System.Text.Json;
using Rhino;
using Rhino.Display;
using Rhino.DocObjects;
using Rhino.Geometry;
using RhinoSceneFlow.Core;

namespace RhinoSceneFlow.Plugin;

public sealed class PlantInstance
{
    public Guid Asset {get;set;}
    public string Image {get;set;}="";
    public string Sha256 {get;set;}="";
    public string ScientificName {get;set;}="";
    public double WidthMeters {get;set;}
    public double HeightMeters {get;set;}
    public double Scale {get;set;}=1;
    public bool Mirror {get;set;}
    public double AnchorU {get;set;}=.5;
    public double AnchorV {get;set;}
}
public static class PlantService
{
    internal const string Key="RhinoSceneFlow.Plant.v1";
    public static MaterialLibrary Library=>new(Path.Combine(SceneFlowPlugin.Instance.MaterialDirectory,"Plants"));
    internal static readonly Dictionary<uint,Guid> Selected=[];
    private static readonly Dictionary<string,(DateTime Stamp,long Length,RgbaTexture Image)> images=[];
    private static PlantConduit? conduit;
    internal static bool Suppress;
    public static BillboardSettings Settings
    {
        get=>JsonSerializer.Deserialize<BillboardSettings>(SceneFlowPlugin.Instance.Settings.GetString("PlantBillboards","{}"),MaterialLibrary.Json)!;
        set{value.Validate();SceneFlowPlugin.Instance.Settings.SetString("PlantBillboards",JsonSerializer.Serialize(value,MaterialLibrary.Json));SceneFlowPlugin.Instance.SaveSettings();foreach(var d in RhinoDoc.OpenDocuments())d.Views.Redraw();}
    }
    internal static void Start(){conduit=new(){Enabled=true};RhinoDoc.CloseDocument+=Closed;}
    private static void Closed(object? sender,DocumentEventArgs e){Selected.Remove(e.Document.RuntimeSerialNumber);PlantTool.StopDocument(e.Document.RuntimeSerialNumber);}
    internal static void Stop(){RhinoDoc.CloseDocument-=Closed;if(conduit!=null){conduit.Enabled=false;conduit.Release();conduit=null;}images.Clear();Selected.Clear();}
    public static bool IsPlant(RhinoObject obj)=>obj.Attributes.GetUserString(Key)!=null;
    public static PlantInstance? Read(RhinoObject obj)=>obj.Attributes.GetUserString(Key) is string s?JsonSerializer.Deserialize<PlantInstance>(s,MaterialLibrary.Json):null;
    internal static RgbaTexture Image(string path,string hash="")
    {
        var file=new FileInfo(path);if(!file.Exists)throw new FileNotFoundException("植物素材丢失。",path);
        if(images.TryGetValue(path,out var cached)&&cached.Stamp==file.LastWriteTimeUtc&&cached.Length==file.Length)return cached.Image;
        if(hash.Length>0&&!RandomImage.Hash(path).Equals(hash,StringComparison.OrdinalIgnoreCase))throw new InvalidDataException("植物图片校验失败。");
        using var source=new System.Drawing.Bitmap(path);if(source.Width>8192||source.Height>8192)throw new ArgumentException("植物 PNG 最大 8192 像素。");
        using var bitmap=new System.Drawing.Bitmap(source.Width,source.Height,PixelFormat.Format32bppArgb);using(var g=System.Drawing.Graphics.FromImage(bitmap))g.DrawImageUnscaled(source,0,0);
        var bits=bitmap.LockBits(new(0,0,bitmap.Width,bitmap.Height),ImageLockMode.ReadOnly,PixelFormat.Format32bppArgb);var rgba=new byte[bitmap.Width*bitmap.Height*4];var row=new byte[bitmap.Width*4];
        try{for(int y=0;y<bitmap.Height;y++){Marshal.Copy(bits.Scan0+y*bits.Stride,row,0,row.Length);for(int x=0;x<bitmap.Width;x++){int p=(y*bitmap.Width+x)*4;rgba[p]=row[x*4+2];rgba[p+1]=row[x*4+1];rgba[p+2]=row[x*4];rgba[p+3]=row[x*4+3];}}}finally{bitmap.UnlockBits(bits);}
        var result=new RgbaTexture(bitmap.Width,bitmap.Height,rgba);if(images.Count>=32||images.Values.Sum(v=>v.Image.Pixels.LongLength)+rgba.LongLength>256L*1024*1024)images.Clear();images[path]=(file.LastWriteTimeUtc,file.Length,result);return result;
    }
    public static MaterialAsset Import(MaterialAsset asset,string path)
    {
        if(asset.Plant==null)throw new ArgumentException("需要植物科学分类。");asset.Plant.Validate();
        var image=Image(path);int transparent=0,visible=0,left=image.Width,top=image.Height,right=0,bottom=0;
        for(int y=0;y<image.Height;y++)for(int x=0;x<image.Width;x++){byte a=image.Pixels[(y*image.Width+x)*4+3];if(a==0)transparent++;if(a>2){visible++;left=Math.Min(left,x);right=Math.Max(right,x+1);top=Math.Min(top,y);bottom=Math.Max(bottom,y+1);}}
        if(transparent<image.Width*image.Height*.01||visible<16)throw new ArgumentException("植物必须是含真实透明背景与可见植株的 PNG，不能使用白底或棋盘格图片。");
        string temp=Path.Combine(Path.GetTempPath(),"SceneFlowPlant-"+Guid.NewGuid().ToString("N")+".png");
        try
        {
            using var source=new System.Drawing.Bitmap(path);using var crop=source.Clone(new System.Drawing.Rectangle(left,top,right-left,bottom-top),PixelFormat.Format32bppArgb);crop.Save(temp,ImageFormat.Png);
            asset=MaterialLibrary.Clone(asset);asset.WidthMeters=asset.HeightMeters*crop.Width/crop.Height;asset.Randomization=new();
            double weighted=0,total=0;for(int y=Math.Max(top,bottom-Math.Max(2,(bottom-top)/100));y<bottom;y++)for(int x=left;x<right;x++){double a=image.Pixels[(y*image.Width+x)*4+3];weighted+=(x+.5-left)*a;total+=a;}
            asset.Plant!.AnchorU=total>0?Math.Clamp(weighted/total/(right-left),0,1):.5;asset.Plant.AnchorV=0;
            return Library.Import(asset,new Dictionary<string,string>{{"baseColor",temp}});
        }
        finally{if(File.Exists(temp))File.Delete(temp);}
    }
    public static Guid[] Place(RhinoDoc doc,Guid assetId,Point3d[] points,int seed=42,double minScale=1,double maxScale=1,bool mirror=true)
    {
        NamedViewExportService.RequireActive(doc);
        if(points.Length is <1 or >10000||points.Any(p=>!p.IsValid)||!double.IsFinite(minScale)||!double.IsFinite(maxScale)||minScale<=0||maxScale<minScale||maxScale>100)throw new ArgumentException("种植位置或缩放范围无效（最多 10000 株）。");
        var a=Library.Get(assetId);if(a.Plant==null)throw new ArgumentException("不是植物素材。");Library.Verify(a);Image(Library.MapPath(a,"baseColor"),a.Sha256["baseColor"]);
        var random=new Random(seed);var ids=new List<Guid>();uint undo=doc.BeginUndoRecord("SceneFlow 种植");
        try
        {
            foreach(var p in points)
            {
                var item=new PlantInstance{Asset=a.Id,Image=Library.MapPath(a,"baseColor"),Sha256=a.Sha256["baseColor"],ScientificName=a.Plant.ScientificName,WidthMeters=a.WidthMeters,HeightMeters=a.HeightMeters,Scale=minScale+random.NextDouble()*(maxScale-minScale),Mirror=mirror&&random.NextDouble()<.5,AnchorU=a.Plant.AnchorU,AnchorV=a.Plant.AnchorV};
                var attrs=new ObjectAttributes{Name=a.Plant.ScientificName+" · "+(ids.Count+1).ToString("000")};attrs.SetUserString(Key,JsonSerializer.Serialize(item,MaterialLibrary.Json));var id=doc.Objects.AddPoint(p,attrs);if(id==Guid.Empty)throw new InvalidOperationException("无法建立植物对象。");ids.Add(id);
            }
        }
        catch{foreach(var id in ids)doc.Objects.Delete(id,true);throw;}
        finally{if(undo!=0)doc.EndUndoRecord(undo);doc.Views.Redraw();}Selected[doc.RuntimeSerialNumber]=assetId;return ids.ToArray();
    }
    public static object Scatter(RhinoDoc doc,Guid asset,Guid surfaceId,int count,double spacingMeters,int seed,double minScale,double maxScale,bool mirror)
    {
        NamedViewExportService.RequireActive(doc);if(count<1||count>10000||!double.IsFinite(spacingMeters)||spacingMeters<0)throw new ArgumentException("数量或间距无效。");
        var obj=doc.Objects.FindId(surfaceId)??throw new ArgumentException("种植曲面不存在。");using var geometry=obj.Geometry.Duplicate();using var mesh=new Mesh();
        if(geometry is Mesh m)mesh.Append(m);
        else
        {
            using var brep=geometry switch{Brep b=>b.DuplicateBrep(),Extrusion e=>e.ToBrep(),Surface s=>s.ToBrep(),_=>throw new ArgumentException("选择网格、曲面或多重曲面区域。")};
            foreach(var part in Mesh.CreateFromBrep(brep,MeshingParameters.Default)??[]){mesh.Append(part);part.Dispose();}
        }
        mesh.Faces.ConvertQuadsToTriangles();var cumulative=new List<double>();double area=0;
        foreach(var f in mesh.Faces){var a=(Point3d)mesh.Vertices[f.A];var b=(Point3d)mesh.Vertices[f.B];var c=(Point3d)mesh.Vertices[f.C];area+=Vector3d.CrossProduct(b-a,c-a).Length*.5;cumulative.Add(area);}
        if(area<=0)throw new ArgumentException("区域没有有效面积。");
        double spacing=spacingMeters*RhinoMath.UnitScale(UnitSystem.Meters,doc.ModelUnitSystem);var cells=new Dictionary<(long,long,long),List<Point3d>>();var points=new List<Point3d>();var rng=new Random(seed);
        for(int attempt=0;attempt<Math.Min(2_000_000,count*300)&&points.Count<count;attempt++)
        {
            int index=cumulative.BinarySearch(rng.NextDouble()*area);if(index<0)index=~index;index=Math.Min(index,mesh.Faces.Count-1);var f=mesh.Faces[index];double u=Math.Sqrt(rng.NextDouble()),v=rng.NextDouble();
            var a=(Point3d)mesh.Vertices[f.A];var p=a+(mesh.Vertices[f.B]-a)* (u*(1-v))+(mesh.Vertices[f.C]-a)*(u*v);
            var key=spacing>0?((long)Math.Floor(p.X/spacing),(long)Math.Floor(p.Y/spacing),(long)Math.Floor(p.Z/spacing)):(0L,0L,0L);bool valid=true;
            if(spacing>0)for(int x=-1;x<=1;x++)for(int y=-1;y<=1;y++)for(int z=-1;z<=1;z++)if(cells.TryGetValue((key.Item1+x,key.Item2+y,key.Item3+z),out var near)&&near.Any(q=>q.DistanceToSquared(p)<spacing*spacing))valid=false;
            if(!valid)continue;points.Add(p);if(!cells.TryGetValue(key,out var cell))cells[key]=cell=[];cell.Add(p);
        }
        if(points.Count==0)throw new InvalidOperationException("间距限制下无法放置植物。");var ids=Place(doc,asset,points.ToArray(),seed,minScale,maxScale,mirror);return new{objects=ids,requested=count,placed=ids.Length,limited=ids.Length<count};
    }
    internal static PlantBillboard Billboard(RhinoDoc doc,RhinoObject obj)
    {
        var item=Read(obj)??throw new ArgumentException("不是植物对象。");if(obj.Geometry is not Rhino.Geometry.Point point)throw new InvalidDataException("植物锚点类型无效。");
        double scale=RhinoMath.UnitScale(UnitSystem.Meters,doc.ModelUnitSystem)*item.Scale;
        if(!double.IsFinite(scale)||scale<=0||!double.IsFinite(item.WidthMeters)||item.WidthMeters<=0||!double.IsFinite(item.HeightMeters)||item.HeightMeters<=0)throw new InvalidDataException("植物尺寸无效。");
        return new(obj.Id.ToString(),item.ScientificName,obj.Name,new(point.Location.X,point.Location.Y,point.Location.Z),item.WidthMeters*scale,item.HeightMeters*scale,item.AnchorU,item.AnchorV,item.Mirror,Image(item.Image,item.Sha256));
    }
    internal static PlantBillboard[] Snapshot(RhinoDoc doc,RhinoViewport viewport)
    {
        var result=new List<PlantBillboard>();var used=new HashSet<string>();long bytes=0;
        foreach(var obj in Visible(doc,viewport))
        {
            var item=Billboard(doc,obj);if(used.Add(Read(obj)!.Image))bytes+=item.Image.Pixels.LongLength;
            if(bytes>512L*1024*1024)throw new InvalidOperationException("当前视图的独立植物图片超过 512 MiB，请减少图片分辨率或种类。");result.Add(item);
        }
        return result.ToArray();
    }
    internal static RhinoObject[] Visible(RhinoDoc doc,RhinoViewport vp)=>doc.Objects.GetObjectList(new ObjectEnumeratorSettings{NormalObjects=true,LockedObjects=true,HiddenObjects=false,VisibleFilter=true,ViewportFilter=vp,IdefObjects=false}).Where(IsPlant).Where(o=>
    {var layer=doc.Layers[o.Attributes.LayerIndex];var seen=new HashSet<Guid>();while(layer!=null){if(!seen.Add(layer.Id)||!layer.IsVisible||!layer.PerViewportIsVisible(vp.Id))return false;if(layer.ParentLayerId==Guid.Empty)return true;layer=doc.Layers.FindId(layer.ParentLayerId);}return false;}).ToArray();
    internal static CameraProjection Camera(RhinoViewport vp)
    {vp.GetFrustum(out double l,out double r,out double b,out double t,out double n,out double f);Vec3 V(Vector3d v)=>new(v.X,v.Y,v.Z);var p=vp.CameraLocation;return new(new(p.X,p.Y,p.Z),V(vp.CameraX),V(vp.CameraY),V(vp.CameraZ),l,r,b,t,n,f,vp.IsParallelProjection);}
}

internal sealed class PlantConduit:DisplayConduit
{
    private readonly Dictionary<(string Path,int Resolution),PlantPreviewGeometry> previews=[];
    protected override void PreDrawObject(DrawObjectEventArgs e){if(PlantService.IsPlant(e.RhinoObject))e.DrawObject=false;}
    protected override void CalculateBoundingBox(CalculateBoundingBoxEventArgs e)
    {
        if(PlantService.Suppress)return;
        foreach(var obj in PlantService.Visible(e.RhinoDoc,e.Viewport))
        {
            if(obj.Geometry is not Rhino.Geometry.Point point)continue;var item=PlantService.Read(obj)!;double r=Math.Max(item.WidthMeters,item.HeightMeters)*item.Scale*RhinoMath.UnitScale(UnitSystem.Meters,e.RhinoDoc.ModelUnitSystem);var d=new Vector3d(r,r,r);e.IncludeBoundingBox(new(point.Location-d,point.Location+d));
        }
    }
    protected override void CalculateBoundingBoxZoomExtents(CalculateBoundingBoxEventArgs e)=>CalculateBoundingBox(e);
    protected override void PostDrawObjects(DrawEventArgs e)
    {
        if(PlantService.Suppress)return;var camera=PlantService.Camera(e.Viewport);var settings=PlantService.Settings;
        foreach(var obj in PlantService.Visible(e.RhinoDoc,e.Viewport).OrderBy(o=>((Rhino.Geometry.Point)o.Geometry).Location.DistanceToSquared(e.Viewport.CameraLocation)).Reverse())
        {
            try
            {
                var p=PlantService.Billboard(e.RhinoDoc,obj);var axes=p.Axes(camera,settings);
                // Display-only depth separation prevents top-facing cards fighting the ground. The stored anchor stays fixed.
                var depthOffset=camera.Back*(Math.Max(p.Width,p.Height)*1e-5);
                Point3d P(double u,double v){var q=p.Anchor+axes.Right*((u-p.PivotU)*p.Width)+axes.Up*((v-p.AnchorV)*p.Height)+depthOffset;return new(q.X,q.Y,q.Z);}
                var pa=camera.Project(p.Anchor);var pb=camera.Project(p.Anchor+axes.Up*p.Height);double screen=pa.W>0&&pb.W>0?Math.Abs(pa.Y/pa.W-pb.Y/pb.W)*e.Viewport.Size.Height/2:512;
                int resolution=screen>384?512:256;string path=PlantService.Read(obj)!.Image;var key=(path,resolution);
                if(!previews.TryGetValue(key,out var preview))
                {
                    preview=new(path,p.Image,resolution);
                    if(previews.Count>=16||previews.Values.Sum(v=>v.Bytes)+preview.Bytes>256L*1024*1024){foreach(var old in previews.Values)old.Dispose();previews.Clear();}
                    previews[key]=preview;
                }
                var x=axes.Right*(p.Width*(p.Mirror?-1:1));var y=axes.Up*p.Height;var origin=p.Anchor-x*p.AnchorU-y*p.AnchorV+depthOffset;
                var normal=axes.Right.Cross(axes.Up);var transform=Transform.Identity;transform.M00=x.X;transform.M10=x.Y;transform.M20=x.Z;transform.M01=y.X;transform.M11=y.Y;transform.M21=y.Z;transform.M02=normal.X;transform.M12=normal.Y;transform.M22=normal.Z;transform.M03=origin.X;transform.M13=origin.Y;transform.M23=origin.Z;
                e.Display.PushModelTransform(transform);
                try{for(int i=7;i>=0;i--)if(preview.Meshes[i].Faces.Count>0)e.Display.DrawMeshShaded(preview.Meshes[i],preview.Materials[i]);}
                finally{e.Display.PopModelTransform();}
                if(obj.IsSelected(false)>0)e.Display.DrawPolyline(new[]{P(0,0),P(1,0),P(1,1),P(0,1),P(0,0)},System.Drawing.Color.Yellow,1);
            }
            catch(Exception ex){System.Diagnostics.Debug.WriteLine("SceneFlow plant: "+ex.Message);}
        }
    }
    internal void Release(){foreach(var p in previews.Values)p.Dispose();previews.Clear();}
}

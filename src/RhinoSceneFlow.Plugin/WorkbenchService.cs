using System.Diagnostics;
using System.Drawing.Imaging;
using System.Runtime.InteropServices;
using Rhino;
using Rhino.Display;
using Rhino.DocObjects;
using Rhino.Geometry;
using RhinoSceneFlow.Core;

namespace RhinoSceneFlow.Plugin;

public sealed record WorkbenchPlan(ViewExportRow View,string Path,bool Overwrite);

public static class WorkbenchService
{
    public static ViewExportRow[] Settings(RhinoDoc doc)
    {
        NamedViewExportService.RequireActive(doc);
        var current=ExportPanelController.Find(doc.RuntimeSerialNumber)?.Views.ToArray()??WorkbenchStore.Load(doc);
        var old=current.GroupBy(r=>r.Id).ToDictionary(g=>g.Key,g=>g.First());
        return NamedViewExportService.List(doc).Select(v=>{var r=old.GetValueOrDefault(v.Id)?.Copy()??new(){Id=v.Id,Width=v.Width,Height=v.Height};r.Name=v.Name;return r;}).ToArray();
    }
    public static void Configure(RhinoDoc doc,ViewExportRow row)
    {
        if(ExportPanelController.Find(doc.RuntimeSerialNumber)?.IsExporting==true)throw new InvalidOperationException("正在导出，请完成或取消后修改配置。");
        row.Validate();using var view=Find(doc,row.Id);row.Name=view.Name;
        var rows=Settings(doc);int index=Array.FindIndex(rows,r=>r.Id==row.Id);if(index<0)throw new ArgumentException("视图不存在。");
        rows[index]=row.Copy();WorkbenchStore.Save(doc,rows);ExportPanelController.Find(doc.RuntimeSerialNumber)?.SetView(row);
    }
    public static DisplayModeDescription[] Modes()=>DisplayModeDescription.GetDisplayModes().Where(m=>m.EnglishName!="Raytraced").ToArray();
    internal static ViewInfo Find(RhinoDoc doc,Guid id)
    {
        for(int i=0;i<doc.NamedViews.Count;i++){var v=doc.NamedViews[i];if(v.NamedViewId==id)return v;v.Dispose();}
        throw new ArgumentException("Named View 已删除，请刷新列表。");
    }
    public static void ApplyCamera(RhinoDoc doc,ViewExportRow row,RhinoViewport viewport,int width,int height)
    {
        using var named=Find(doc,row.Id);using var info=new ViewportInfo(named.Viewport);
        if(named.ClippingPlanesIds.Length>0)throw new NotSupportedException("暂不支持关联裁剪平面的 Named View。");
        info.ScreenPort=new(0,0,width,height);info.FrustumAspect=(double)width/height;
        if(!viewport.SetViewProjection(info,true))throw new InvalidOperationException("无法设置 Named View 相机。");
        var c=row.Camera;
        if(c.Yaw==0&&c.Pitch==0&&c.Zoom==1&&c.PanX==0&&c.PanY==0&&c.PanZ==0)return;
        // CameraTarget on a borrowed view and on a standalone viewport can differ.
        // Derive one orbit pivot from the saved Named View, never from the host view.
        var position=info.CameraLocation;var up=info.CameraUp;var axis=info.CameraDirection;axis.Unitize();
        var savedTarget=info.TargetPoint;
        double distance=savedTarget.IsValid?(savedTarget-position)*axis:double.NaN;
        if(!double.IsFinite(distance)||distance<=1e-8)
        {var box=doc.Objects.BoundingBoxVisible;distance=box.IsValid?(box.Center-position)*axis:100;if(distance<=1e-8)distance=100;}
        var target=position+axis*distance;
        var offset=new Vector3d(c.PanX,c.PanY,c.PanZ);target+=offset;position+=offset;
        var yaw=Transform.Rotation(c.Yaw*Math.PI/180,Vector3d.ZAxis,target);position.Transform(yaw);up.Transform(yaw);
        var direction=target-position;var right=Vector3d.CrossProduct(direction,up);right.Unitize();
        var pitch=Transform.Rotation(c.Pitch*Math.PI/180,right,target);position.Transform(pitch);up.Transform(pitch);
        viewport.SetCameraLocations(target,position);
        using(var adjusted=new ViewportInfo(viewport)){adjusted.SetCameraUp(up);viewport.SetViewProjection(adjusted,true);}
        if(Math.Abs(c.Zoom-1)>1e-12)
        {
            using var zoomed=new ViewportInfo(viewport);
            viewport.GetFrustum(out double l,out double r,out double b,out double t,out double n,out double f);
            zoomed.SetFrustum(l/c.Zoom,r/c.Zoom,b/c.Zoom,t/c.Zoom,n,f);viewport.SetViewProjection(zoomed,true);
        }
    }
    public static WorkbenchPlan[] Plan(RhinoDoc doc,IEnumerable<ViewExportRow> source,string directory,Func<string,FileCollision> collision)
    {
        NamedViewExportService.RequireActive(doc);var rows=source.Where(v=>v.Included).Select(v=>v.Copy()).ToArray();
        if(rows.Length==0)throw new ArgumentException("请勾选需要导出的视图。");
        if(!Path.IsPathFullyQualified(directory))throw new ArgumentException("请选择绝对路径的输出文件夹。");
        if(rows.Select(r=>r.Id).Distinct().Count()!=rows.Length)throw new ArgumentException("视图不能重复。");
        // Every view is checked before collision prompts or pixel capture.
        foreach(var row in rows)
        {
            row.Validate();using var saved=Find(doc,row.Id);
            if(saved.ClippingPlanesIds.Length>0)throw new NotSupportedException("暂不支持关联裁剪平面的视图。");
            row.Name=saved.Name;
            if((long)row.Width*row.Height*4*(row.Layers.Count(l=>l.Enabled)+1)>1_990_000_000)throw new ArgumentException("预计 PSD 超过 2 GB，请减少尺寸或图层。");
        }
        var reserved=new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        return rows.Select(row=>{var output=OutputNames.Reserve(Path.GetFullPath(directory),row.Name,reserved,collision);return new WorkbenchPlan(row,output.Path,output.Overwrite);}).ToArray();
    }
    public static System.Drawing.Bitmap Preview(RhinoDoc doc,ViewExportRow row,int longest=360)
    {
        NamedViewExportService.RequireActive(doc);
        if(row.Width<64||row.Height<64)throw new ArgumentException("宽高至少 64 像素。");
        double scale=(double)longest/Math.Max(row.Width,row.Height);
        int w=Math.Max(1,(int)Math.Round(row.Width*scale)),h=Math.Max(1,(int)Math.Round(row.Height*scale));
        using var scope=new CaptureScope(doc,row,row.Width,row.Height);
        return scope.Capture(row.Mode,w,h);
    }
    public static void WriteBack(RhinoDoc doc,ViewExportRow row)
    {
        NamedViewExportService.RequireActive(doc);using var viewport=new RhinoViewport();
        viewport.Size=new(row.Width,row.Height);ApplyCamera(doc,row,viewport,row.Width,row.Height);
        using var view=new ViewInfo(viewport){Name=row.Name};
        int index=doc.NamedViews.Add(view);if(index<0)throw new InvalidOperationException("无法写回 Named View。");
        using var saved=doc.NamedViews[index];row.Id=saved.NamedViewId;row.Camera=new();
    }
    internal static PreparedWorkbench Prepare(RhinoDoc doc,WorkbenchPlan plan,CancellationToken token)
    {
        NamedViewExportService.RequireActive(doc);plan.View.Validate();
        foreach(var o in doc.Objects.GetObjectList(ObjectType.ClipPlane))
            if(o.Geometry is ClippingPlaneSurface cp&&cp.ViewportIds().Contains(doc.Views.ActiveView.ActiveViewport.Id))throw new NotSupportedException("当前模型视图关联裁剪平面。");
        var prepared=new PreparedWorkbench(plan);
        try
        {
            token.ThrowIfCancellationRequested();var row=plan.View;
            using(var scope=new CaptureScope(doc,row,row.Width,row.Height))
            {
                prepared.Light=scope.ToSun;
                foreach(var mode in Modes())prepared.ModeNames[mode.Id]=mode.LocalName;
                foreach(var layer in row.Layers.Where(l=>l.Enabled&&l.Kind=="display").DistinctBy(l=>l.Mode))
                {
                    token.ThrowIfCancellationRequested();
                    using var bitmap=scope.Capture(layer.Mode,row.Width,row.Height);
                    var image=new DiskPassImage(prepared.Staging,row.Width,row.Height,[new("Display",new(0,0,0))],true);
                    prepared.Display.Add(layer.Mode,image);
                    var bits=bitmap.LockBits(new(0,0,bitmap.Width,bitmap.Height),ImageLockMode.ReadOnly,PixelFormat.Format32bppArgb);
                    try
                    {
                        var bgra=new byte[bitmap.Width*4];var rgba=new byte[bgra.Length];
                        for(int y=0;y<bitmap.Height;y++)
                        {
                            token.ThrowIfCancellationRequested();Marshal.Copy(bits.Scan0+y*bits.Stride,bgra,0,bgra.Length);
                            for(int x=0;x<bitmap.Width;x++){rgba[x*4]=bgra[x*4+2];rgba[x*4+1]=bgra[x*4+1];rgba[x*4+2]=bgra[x*4];rgba[x*4+3]=bgra[x*4+3];}
                            image.WriteRgbaRow(y,0,rgba);
                        }
                    }
                    finally{bitmap.UnlockBits(bits);}
                }
            }
            if(row.Layers.Any(l=>l.Enabled&&l.Kind is "material" or "shadow"))
            {
                prepared.Viewport=new RhinoViewport();prepared.Viewport.Size=new(row.Width,row.Height);ApplyCamera(doc,row,prepared.Viewport,row.Width,row.Height);
                prepared.Reader=new(doc,prepared.Viewport,token,true,row.Layers.Any(l=>l.Enabled&&l.Kind=="shadow")){VisibilityViewport=doc.Views.ActiveView.ActiveViewport};
                prepared.Triangles=prepared.Reader.Read().ToArray();
                prepared.Shadow=new(prepared.Light,new(90,90,90),true,Math.Max(doc.ModelAbsoluteTolerance*.001,1e-7));
            }
            return prepared;
        }
        catch{prepared.Dispose();throw;}
    }
    public static BatchReport Export(RhinoDoc doc,WorkbenchPlan[] plan,CancellationToken token=default)
    {
        var results=new List<BatchFileResult>();
        foreach(var item in plan)
        {
            try{token.ThrowIfCancellationRequested();using var prepared=Prepare(doc,item,token);results.Add(prepared.Write(token));}
            catch(OperationCanceledException){return new(results.ToArray(),true);}
            catch(Exception ex){results.Add(new(item.View.Id,item.View.Name,item.Path,false,item.View.Width,item.View.Height,0,0,ex.Message));}
        }
        return new(results.ToArray(),false);
    }
}

/// <summary>One existing model view is borrowed on the UI thread, always restored.</summary>
internal sealed class CaptureScope : IDisposable
{
    private readonly RhinoDoc doc;
    private readonly RhinoView view;
    private readonly ViewportInfo saved;
    private readonly DisplayModeDescription mode;
    private readonly string name;
    private readonly bool modified,redraw,grid,axes,worldAxes;
    private Rhino.Render.RenderSettings? render;
    public Vec3 ToSun{get;private set;}
    public CaptureScope(RhinoDoc doc,ViewExportRow row,int width,int height)
    {
        this.doc=doc;view=doc.Views.ActiveView;var vp=view.ActiveViewport;saved=new(vp);mode=vp.DisplayMode;name=vp.Name;
        modified=doc.Modified;redraw=doc.Views.RedrawEnabled;grid=vp.ConstructionGridVisible;axes=vp.ConstructionAxesVisible;worldAxes=vp.WorldAxesVisible;
        try
        {
            doc.Views.RedrawEnabled=false;WorkbenchService.ApplyCamera(doc,row,vp,width,height);
            vp.ConstructionGridVisible=vp.ConstructionAxesVisible=vp.WorldAxesVisible=false;
            if(!row.Sun.UseDocument)
            {
                render=doc.RenderSettings.Duplicate();var sun=doc.RenderSettings.Sun;
                sun.BeginChange(Rhino.Render.RenderContent.ChangeContexts.Program);
                try{sun.ManualControlOn=true;sun.Azimuth=row.Sun.Azimuth;sun.Altitude=row.Sun.Altitude;sun.Enabled=true;}
                finally{sun.EndChange();}
            }
            var s=doc.RenderSettings.Sun;var d=s.Vector;
            ToSun=s.Enabled&&d.IsValid&&d.Length>0&&d.Z<0?new Vec3(-d.X,-d.Y,-d.Z).Unit:new Vec3(-1,-1,2).Unit;
        }
        catch{Dispose();throw;}
    }
    public System.Drawing.Bitmap Capture(Guid modeId,int width,int height)
    {
        var display=WorkbenchService.Modes().FirstOrDefault(m=>m.Id==modeId)??throw new ArgumentException("显示模式已删除或不支持捕获。");
        var attributes=display.DisplayAttributes;bool highlights=attributes.IgnoreHighlights;
        try{attributes.IgnoreHighlights=true;return view.CaptureToBitmap(new System.Drawing.Size(width,height),attributes)??throw new InvalidOperationException("Rhino 无法捕获该显示模式。");}
        finally{attributes.IgnoreHighlights=highlights;}
    }
    public void Dispose()
    {
        var vp=view.ActiveViewport;vp.SetViewProjection(saved,true);vp.DisplayMode=mode;vp.Name=name;
        vp.ConstructionGridVisible=grid;vp.ConstructionAxesVisible=axes;vp.WorldAxesVisible=worldAxes;
        if(render is not null){doc.RenderSettings=render;render.Dispose();render=null;}
        doc.Modified=modified;doc.Views.RedrawEnabled=redraw;saved.Dispose();
    }
}

internal sealed class PreparedWorkbench(WorkbenchPlan plan) : IDisposable
{
    private readonly Stopwatch watch=Stopwatch.StartNew();
    internal readonly string Staging=Directory.CreateTempSubdirectory("RhinoSceneFlow-").FullName;
    internal readonly Dictionary<Guid,DiskPassImage> Display=[];
    internal readonly Dictionary<Guid,string> ModeNames=[];
    internal RhinoViewport? Viewport;
    internal SceneReader? Reader;
    internal Triangle[] Triangles=[];
    internal ShadowSettings? Shadow;
    internal Vec3 Light;
    private readonly List<DiskPassImage> staged=[];
    public BatchFileResult Write(CancellationToken token)
    {
        var row=plan.View;int w=row.Width,h=row.Height;
        DiskPassImage? material=null,shadow=null;
        if(row.Layers.Any(l=>l.Enabled&&l.Kind=="material")){material=new(Staging,w,h,Reader!.Groups);staged.Add(material);}
        if(row.Layers.Any(l=>l.Enabled&&l.Kind=="shadow")){shadow=new(Staging,w,h,[new("Shadow",new(90,90,90))]);staged.Add(shadow);}
        if(material is not null||shadow is not null)
        {
            var camera=Reader!.Camera;var world=Reader.WorldTriangles;const int tileSize=1024;
            for(int top=0;top<h;top+=tileSize)for(int left=0;left<w;left+=tileSize)
            {
                token.ThrowIfCancellationRequested();int tw=Math.Min(tileSize,w-left),th=Math.Min(tileSize,h-top);
                int x0=Math.Max(0,left-2),y0=Math.Max(0,top-2),x1=Math.Min(w,left+tw+2),y1=Math.Min(h,top+th+2);
                int rw=x1-x0,rh=y1-y0;
                var tile=camera with{Left=camera.Left+(camera.RightEdge-camera.Left)*x0/w,RightEdge=camera.Left+(camera.RightEdge-camera.Left)*x1/w,
                    Top=camera.Top-(camera.Top-camera.Bottom)*y0/h,Bottom=camera.Top-(camera.Top-camera.Bottom)*y1/h};
                if(material is not null)
                {
                    var triangles=world.Select((t,i)=>new Triangle(tile.Project(t.A),tile.Project(t.B),tile.Project(t.C),Triangles[i].Group));
                    material.WriteTile(left,top,new ImageWindow(FlatRasterizer.Render(rw,rh,Reader.Groups,triangles,token),left-x0,top-y0,tw,th),token);
                }
                if(shadow is not null)
                {
                    shadow.WriteTile(left,top,new ImageWindow(ShadowVolumeRenderer.Render(rw,rh,tile,world,Shadow!,token,Reader.Surfaces!.Evaluator(tile,rw,rh,Shadow!)),left-x0,top-y0,tw,th),token);
                    Reader.Surfaces!.ReleaseEvaluators();
                }
            }
        }
        var passes=row.Layers.Where(l=>l.Enabled).Select(l=>new StyledPass(l.Kind=="material"?"材质 / 图层色":l.Kind=="shadow"?"Shadow":ModeNames[l.Mode],
            l.Kind=="material"?material!:l.Kind=="shadow"?shadow!:Display[l.Mode],l.Blend,(byte)Math.Round(l.Opacity*255.0/100),l.Kind=="material")).ToArray();
        var image=new ConfiguredStack(passes);Directory.CreateDirectory(Path.GetDirectoryName(plan.Path)!);
        int count=PsdWriter.Save(plan.Path,image,token,plan.Overwrite,true);
        return new(row.Id,row.Name,plan.Path,true,w,h,count,watch.ElapsedMilliseconds,null);
    }
    public void Dispose()
    {
        foreach(var image in staged)image.Dispose();foreach(var image in Display.Values)image.Dispose();
        Reader?.Dispose();Viewport?.Dispose();if(Directory.Exists(Staging))Directory.Delete(Staging,true);
    }
}

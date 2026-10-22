using System.Diagnostics;
using Rhino;
using Rhino.Display;
using Rhino.DocObjects;
using RhinoSceneFlow.Core;

namespace RhinoSceneFlow.Plugin;

public sealed record NamedViewSpec(Guid ViewId,int Width,int Height);
public sealed record NamedViewEntry(Guid Id,string Name,int Width,int Height);
public sealed record BatchChannels(bool Material=true,bool Shadow=true);
public sealed record NamedViewPlan(NamedViewSpec View,string Name,string Path,bool Overwrite);
public sealed record BatchFileResult(Guid ViewId,string Name,string Path,bool Ok,int Width,int Height,int Layers,long Milliseconds,string? Error);
public sealed record BatchReport(BatchFileResult[] Files,bool Cancelled);

/// <summary>Shared UI/MCP batch service. Never restores views into a document viewport.</summary>
public static class NamedViewExportService
{
    public static void RequireActive(RhinoDoc doc)
    {
        if(RhinoApp.InvokeRequired)throw new InvalidOperationException("Use the Rhino UI thread to read Named Views.");
        if(doc.IsHeadless || RhinoDoc.ActiveDoc?.RuntimeSerialNumber!=doc.RuntimeSerialNumber)
            throw new InvalidOperationException("请激活此面板所属的 Rhino 文档。");
        if(doc.Views.ActiveView is null || doc.Views.ActiveView is RhinoPageView)
            throw new NotSupportedException("请先激活模型视图，暂不支持布局。");
    }
    public static NamedViewEntry[] List(RhinoDoc doc)
    {
        RequireActive(doc);var items=new List<NamedViewEntry>();
        for(int i=0;i<doc.NamedViews.Count;i++)
        {
            using var view=doc.NamedViews[i];
            double aspect=view.Viewport.FrustumAspect;
            if(!double.IsFinite(aspect)||aspect<=0)aspect=1.6;
            int width=2048,height=Math.Clamp((int)Math.Round(width/aspect),64,8192);
            if((long)width*height>8_000_000)width=Math.Max(64,8_000_000/height);
            items.Add(new(view.NamedViewId,view.Name,width,height));
        }
        return items.ToArray();
    }
    private static ViewInfo Find(RhinoDoc doc,Guid id)
    {
        for(int i=0;i<doc.NamedViews.Count;i++)
        {
            var v=doc.NamedViews[i];if(v.NamedViewId==id)return v;v.Dispose();
        }
        throw new ArgumentException("Named View 已删除，请刷新列表。");
    }
    public static void ApplyCamera(RhinoDoc doc,Guid id,RhinoViewport target,int width,int height)
    {
        RequireActive(doc);ValidateSize(width,height);
        using var saved=Find(doc,id);
        using var info=new ViewportInfo(saved.Viewport);
        info.ScreenPort=new System.Drawing.Rectangle(0,0,width,height);
        info.FrustumAspect=(double)width/height;
        if(!target.SetViewProjection(info,true))throw new InvalidOperationException("无法读取 Named View 相机。");
    }
    public static void ValidateSize(int width,int height)
    {
        if(width<64||height<64||width>8192||height>8192||(long)width*height>8_000_000)
            throw new ArgumentOutOfRangeException(nameof(width),"宽高均需 64–8192 像素，总像素不超过 800 万。");
    }
    public static NamedViewPlan[] Plan(RhinoDoc doc,IReadOnlyList<NamedViewSpec> views,string directory,BatchChannels channels,Func<string,FileCollision> resolve)
    {
        RequireActive(doc);
        if(!channels.Material&&!channels.Shadow)throw new ArgumentException("至少选择一个导出通道。");
        if(views.Count==0)throw new ArgumentException("请勾选需要导出的 Named View。");
        if(views.Select(v=>v.ViewId).Distinct().Count()!=views.Count)throw new ArgumentException("同一 Named View 不能重复添加。");
        if(!Path.IsPathFullyQualified(directory))throw new ArgumentException("请选择绝对路径的输出文件夹。");
        directory=Path.GetFullPath(directory);
        var names=new List<(NamedViewSpec Spec,string Name)>();
        foreach(var v in views)
        {
            ValidateSize(v.Width,v.Height);using var saved=Find(doc,v.ViewId);
            if(saved.ClippingPlanesIds.Length>0)throw new NotSupportedException($"{saved.Name} 关联裁剪平面，暂不支持导出。");
            names.Add((v,saved.Name));
        }
        var reserved=new HashSet<string>(StringComparer.OrdinalIgnoreCase);var result=new List<NamedViewPlan>();
        // Resolve all existing filenames before rendering or overwriting any file.
        foreach(var (spec,name) in names)
        {
            var path=OutputNames.Reserve(directory,name,reserved,resolve);
            result.Add(new(spec,name,path.Path,path.Overwrite));
        }
        return result.ToArray();
    }
    internal static PreparedNamedExport Prepare(RhinoDoc doc,NamedViewPlan plan,BatchChannels channels,CancellationToken cancellation)
    {
        RequireActive(doc);using var named=Find(doc,plan.View.ViewId);
        if(named.ClippingPlanesIds.Length>0)throw new NotSupportedException("Named View 关联裁剪平面。");
        var physical=doc.Views.ActiveView.ActiveViewport;
        foreach(var o in doc.Objects.GetObjectList(Rhino.DocObjects.ObjectType.ClipPlane))
            if(o.Geometry is Rhino.Geometry.ClippingPlaneSurface cp && cp.ViewportIds().Contains(physical.Id))
                throw new NotSupportedException("当前模型视图关联裁剪平面，暂不支持导出。");
        // The copy constructor retains ParentView; resizing it can resize the main
        // document viewport. A standalone viewport owns its screen port independently.
        var viewport=new RhinoViewport();
        SceneReader? reader=null;
        try
        {
            viewport.Size=new(plan.View.Width,plan.View.Height);
            ApplyCamera(doc,plan.View.ViewId,viewport,plan.View.Width,plan.View.Height);
            // Channel selection must not change the visible mesh or its silhouette.
            reader=new(doc,viewport,cancellation,true,channels.Shadow){VisibilityViewport=physical};
            var triangles=reader.Read().ToArray();
            var sun=doc.RenderSettings.Sun;var direction=sun.Vector;
            var toSun=sun.Enabled && direction.IsValid && direction.Length>0 && direction.Z<0 ?
                new Vec3(-direction.X,-direction.Y,-direction.Z) : new Vec3(-1,-1,2);
            var shadow=new ShadowSettings(toSun.Unit,new(90,90,90),Bias:Math.Max(doc.ModelAbsoluteTolerance*.001,1e-7));
            return new(plan,channels,reader,viewport,triangles,shadow);
        }
        catch{reader?.Dispose();viewport.Dispose();throw;}
    }
    public static BatchReport Export(RhinoDoc doc,NamedViewPlan[] plan,BatchChannels channels,CancellationToken cancellation=default)
    {
        var files=new List<BatchFileResult>();
        foreach(var item in plan)
        {
            if(cancellation.IsCancellationRequested)return new(files.ToArray(),true);
            try{using var prepared=Prepare(doc,item,channels,cancellation);files.Add(prepared.Write(cancellation));}
            catch(OperationCanceledException){return new(files.ToArray(),true);}
            catch(Exception ex){files.Add(Failure(item,ex));}
        }
        return new(files.ToArray(),false);
    }
    internal static BatchFileResult Failure(NamedViewPlan p,Exception ex)=>new(p.View.ViewId,p.Name,p.Path,false,p.View.Width,p.View.Height,0,0,ex.Message);
}

/// <summary>Only immutable scene data and owned geometry copies cross onto a worker thread.</summary>
internal sealed class PreparedNamedExport(NamedViewPlan plan,BatchChannels channels,SceneReader reader,
    RhinoViewport viewport,Triangle[] triangles,ShadowSettings shadow) : IDisposable
{
    private readonly CameraProjection camera=reader.Camera;
    public BatchFileResult Write(CancellationToken cancellation)
    {
        var watch=Stopwatch.StartNew();int w=plan.View.Width,h=plan.View.Height;
        var passes=new List<RasterImage>();
        if(channels.Shadow)
            passes.Add(ShadowVolumeRenderer.Render(w,h,camera,reader.WorldTriangles,shadow,cancellation,
                reader.Surfaces!.Evaluator(camera,w,h,shadow)));
        if(channels.Material)
        {
            var material=FlatRasterizer.Render(w,h,reader.Groups,triangles,cancellation);
            if(material.GetVisibleLayers(cancellation).Count==0)throw new InvalidOperationException("该视图没有可见的材质色层像素。");
            passes.Add(material);
        }
        var image=new LayerStack(passes.ToArray());
        Directory.CreateDirectory(Path.GetDirectoryName(plan.Path)!);
        int layers=PsdWriter.Save(plan.Path,image,cancellation,plan.Overwrite,allowEmpty:true);
        return new(plan.View.ViewId,plan.Name,plan.Path,true,w,h,layers,watch.ElapsedMilliseconds,null);
    }
    public void Dispose(){reader.Dispose();viewport.Dispose();}
}

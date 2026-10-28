using Rhino;
using Rhino.Display;
using Rhino.DocObjects;
using Rhino.Geometry;
using Rhino.PlugIns;
using Rhino.Render;
using Rhino.Render.CustomRenderMeshes;

namespace RhinoSceneFlow.Plugin;

/// <summary>Only UI-thread snapshots enter the cache. Native renderer callbacks
/// return immutable owned primitives and never traverse live document geometry.</summary>
internal sealed class UvRenderProvider : RenderMeshProvider
{
    internal static readonly Guid Id=new("5bf17d96-df90-4c93-8b3e-97d6e42d580f");
    public override Guid ProviderId=>Id;
    public override string Name=>"SceneFlow seam-preserving UV";
    private sealed record Entry(string Key,Rhino.Render.CustomRenderMeshes.RenderMeshes Primitives,Mesh Mesh,RenderMaterial? Material):IDisposable
    {public void Dispose(){Primitives.Dispose();Mesh.Dispose();Material?.Dispose();}}
    private static readonly object gate=new();
    private static readonly Dictionary<(uint,Guid),Entry> entries=[];
    private static readonly List<(Entry Value,DateTime Release)> retired=[];
    private static long mappingEpoch;
    private static void MappingChanged(object? sender,RhinoDoc.TextureMappingEventArgs args)=>Interlocked.Increment(ref mappingEpoch);
    private static void Retire(Entry entry)=>retired.Add((entry,DateTime.UtcNow.AddSeconds(5)));
    private static uint hash;
    private static DateTime next;
    private static bool started,stopping;
    private static UvRenderProvider? registeredProvider;
    internal static void Start(PlugIn plugin)
    {
        if(started)return;
        var provider=new UvRenderProvider();
        if(!RegisterProvider(provider,plugin))throw new InvalidOperationException("无法注册原生 UV 渲染网格提供器。");
        registeredProvider=provider;
        started=true;RhinoApp.Idle+=Idle;RhinoDoc.TextureMappingEvent+=MappingChanged;
    }
    internal static void Stop()
    {
        stopping=true;RhinoApp.Idle-=Idle;RhinoDoc.TextureMappingEvent-=MappingChanged;
        registeredProvider?.Dispose();registeredProvider=null;
        lock(gate){foreach(var entry in entries.Values)entry.Dispose();foreach(var entry in retired)entry.Value.Dispose();entries.Clear();retired.Clear();}
    }
    public override bool HasCustomRenderMeshes(MeshType mt,ViewportInfo vp,RhinoDoc doc,Guid objectId,ref Flags flags,PlugIn plugin,DisplayPipelineAttributes attrs)
    {lock(gate)return !stopping&&entries.ContainsKey((doc.RuntimeSerialNumber,objectId));}
    public override Rhino.Render.CustomRenderMeshes.RenderMeshes RenderMeshes(MeshType mt,ViewportInfo vp,RhinoDoc doc,Guid objectId,List<InstanceObject> ancestry,ref Flags flags,Rhino.Render.CustomRenderMeshes.RenderMeshes previousPrimitives,PlugIn plugin,DisplayPipelineAttributes attrs)
    {lock(gate)return entries.TryGetValue((doc.RuntimeSerialNumber,objectId),out var entry)?entry.Primitives:previousPrimitives;}
    private static void Idle(object? sender,EventArgs args)
    {
        if(stopping||DateTime.UtcNow<next)return;next=DateTime.UtcNow.AddSeconds(1);
        try
        {
            var alive=new HashSet<(uint,Guid)>();
            foreach(var doc in RhinoDoc.OpenDocuments())foreach(var obj in doc.Objects)
            {
                if(MaterialService.ReadUv(obj) is not {Version:2,MeshChannel:>1})continue;
                alive.Add((doc.RuntimeSerialNumber,obj.Id));Refresh(doc,obj);
            }
            lock(gate)foreach(var key in entries.Keys.Where(k=>!alive.Contains(k)).ToArray()){Retire(entries[key]);entries.Remove(key);}
        }
        catch(Exception e){RhinoApp.WriteLine("SceneFlow UV 渲染缓存："+e.Message);}
        lock(gate)for(int i=retired.Count-1;i>=0;i--)if(retired[i].Release<DateTime.UtcNow){retired[i].Value.Dispose();retired.RemoveAt(i);}
    }
    internal static void Refresh(RhinoDoc doc,RhinoObject obj)
    {
        if(stopping)return;var id=(doc.RuntimeSerialNumber,obj.Id);var record=MaterialService.ReadUv(obj);
        if(record is not {Version:2,MeshChannel:>1}||record.GeometryCrc!=obj.Geometry.DataCRC(0))
        {lock(gate)if(entries.Remove(id,out var old))Retire(old);return;}
        var render=obj.GetRenderMaterial(true);uint materialHash=render?.RenderHash??0;
        string key=MaterialService.Serialize(record)+mappingEpoch+"/"+materialHash+"/"+obj.Attributes.MaterialSource+"/"+obj.Attributes.MaterialIndex;
        lock(gate)if(entries.TryGetValue(id,out var current)&&current.Key==key)return;
        var mesh=MaterialService.UnwrappedMesh(doc,obj);if(mesh==null){lock(gate)if(entries.Remove(id,out var stale))Retire(stale);return;}
        RenderMaterial? material=null;
        try
        {
            material=render?.MakeCopy() as RenderMaterial;
            using var map=TextureMapping.CreateSurfaceParameterMapping();
            mesh.SetTextureCoordinates(map,Transform.Identity,false,true);
            // Native channel 1 now means existing metric mesh UV, never atlas reprojection.
            using var native=material?.ToMaterial(RenderTexture.TextureGeneration.Disallow);
            if(native!=null)mesh.SetCachedTextureCoordinatesFromMaterial(obj,native);
            var primitives=new Rhino.Render.CustomRenderMeshes.RenderMeshes(doc,obj.Id,Id,++hash,(uint)Flags.IsDocumentObject);
            primitives.AddInstance(new Instance{Mesh=mesh,Material=material,Transform=Transform.Identity,IsViewDependent=false,IsRequestingPlugInDependent=false,IsForcedMaterial=false});
            var entry=new Entry(key,primitives,mesh,material);
            lock(gate){if(entries.Remove(id,out var old))Retire(old);entries[id]=entry;}
        }
        catch{mesh.Dispose();material?.Dispose();throw;}
    }
    public static object Status(){lock(gate)return new{registered=started,objects=entries.Count,retired=retired.Count};}
    internal static object Inspect(RhinoDoc doc,Guid id)
    {
        var obj=doc.Objects.FindId(id)??throw new ArgumentException("物件不存在。");Refresh(doc,obj);
        using var expected=MaterialService.UnwrappedMesh(doc,obj)??throw new InvalidOperationException("展开记录缺失或失效。");
        var flags=Flags.IsDocumentObject|Flags.AlwaysCopyDocumentContent;
        using var vp=new ViewportInfo(doc.Views.ActiveView.ActiveViewport);
        using var primitives=obj.RenderMeshes(MeshType.Render,vp,[],ref flags,SceneFlowPlugin.Instance,null);
        var rows=new List<object>();
        foreach(var instance in primitives)
        {
            using var mesh=instance.Mesh;double uvError=0,normalError=0;
            if(mesh.Vertices.Count!=expected.Vertices.Count||mesh.TextureCoordinates.Count!=expected.TextureCoordinates.Count)throw new InvalidOperationException("原生渲染器未使用分岛网格。");
            for(int i=0;i<mesh.Vertices.Count;i++)
            {
                var a=mesh.TextureCoordinates[i];var b=expected.TextureCoordinates[i];uvError=Math.Max(uvError,Math.Max(Math.Abs(a.X-b.X),Math.Abs(a.Y-b.Y)));
                var na=mesh.Normals[i];var nb=expected.Normals[i];normalError=Math.Max(normalError,(na-nb).Length);
            }
            using var volume=mesh.IsClosed?VolumeMassProperties.Compute(mesh):null;
            rows.Add(new{vertices=mesh.Vertices.Count,faces=mesh.Faces.Count,uvError,normalError,volume=volume?.Volume,cachedTextureCoordinates=mesh.HasCachedTextureCoordinates});
        }
        return new{id,sourceCrc=obj.Geometry.DataCRC(0),record=MaterialService.ReadUv(obj),primitives=rows};
    }
}

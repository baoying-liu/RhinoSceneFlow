using System.Security.Cryptography;
using System.Text;
using Rhino;
using Rhino.DocObjects;
using Rhino.Geometry;
using Rhino.Render;
using RhinoSceneFlow.Core;

namespace RhinoSceneFlow.Plugin;

public sealed class WorldUvRecord
{
    public int Version { get; set; } = 1;
    public double UnitScale { get; set; }
    public uint GeometryCrc { get; set; }
    public string MappingHash { get; set; } = "";
    public string Mode { get; set; } = "";
    public MappingSettings Settings { get; set; } = new();
    public int MeshChannel { get; set; }
    public string MeshHash { get; set; } = "";
    public bool OrientationCorrected { get; set; }
}

public static partial class MaterialService
{
    internal const string WorldUvKey="RhinoSceneFlow.WorldUv";
    internal sealed record UvItem(RhinoObject Object,TextureMapping? Mapping,WorldUvRecord Record,string Backup);
    internal sealed class UvPlan : IDisposable
    {
        internal List<UvItem> Items { get; } = [];
        public void Dispose(){foreach(var item in Items)item.Mapping?.Dispose();}
    }
    private static string Hash(string value)=>Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(value)));
    private static string MapHash(TextureMapping map,Transform transform)=>Hash(MappingSnapshot.Fingerprint(map)+Serialize(ToArray(transform)));
    private static bool MapMatches(string expected,TextureMapping map,Transform transform)=>
        expected==MapHash(map,transform)||(map.MappingType==TextureMappingType.MeshMappingPrimitive&&expected==Hash(MappingSnapshot.Capture(map)+Serialize(ToArray(transform))));
    internal static WorldUvRecord? ReadUv(RhinoObject obj)
    {
        var text=obj.Attributes.GetUserString(WorldUvKey);if(text==null)return null;
        try{return Deserialize<WorldUvRecord>(text);}catch{return null;}
    }
    internal static bool UvValid(RhinoDoc doc,RhinoObject obj)
    {
        var r=ReadUv(obj);if(r==null||r.Version is not (1 or 2)||r.UnitScale!=UnitScale(doc)||r.GeometryCrc!=obj.Geometry.DataCRC(0))return false;
        if(r.Version==1&&r.Mode=="xatlas")return false; // Legacy custom projection loses UV islands in native display.
        using var m=obj.GetTextureMapping(1,out var transform);if(m==null)return false;
        try
        {
            if(!MapMatches(r.MappingHash,m,transform))return false;
            if(r.Version==2){using var stored=obj.GetTextureMapping(r.MeshChannel,out var sx);return stored!=null&&MapMatches(r.MeshHash,stored,sx);}
            return true;
        }catch(NotSupportedException){return false;}
    }
    private static object UvStatus(RhinoDoc doc,RhinoObject obj)=>new{valid=UvValid(doc,obj),record=ReadUv(obj),metersPerUv=1};
    public static object InspectWorldUv(RhinoDoc doc,Guid[] objects)=>Targets(doc,objects,null).Select(o=>new{id=o.Id,status=UvStatus(doc,o)}).ToArray();
    public static Guid[] ResolveTargets(RhinoDoc doc,Guid[]? objects,Guid[]? layers)=>Targets(doc,objects,layers).Select(o=>o.Id).ToArray();
    private static string Backup(RhinoObject obj)
    {
        var existing=obj.Attributes.GetUserString(BackupKey);if(existing!=null)return existing;
        using var previous=obj.GetTextureMapping(1,out var transform);
        return Serialize(new MaterialBackup{MaterialSource=(int)obj.Attributes.MaterialSource,MaterialIndex=obj.Attributes.MaterialIndex,RenderMaterial=obj.RenderMaterial?.Id??Guid.Empty,
            Mapping=previous==null?null:MappingSnapshot.Capture(previous),Transform=ToArray(transform),Binding=obj.Attributes.GetUserString(BindingKey),WorldUv=obj.Attributes.GetUserString(WorldUvKey)});
    }
    private static UvPlan PlanUv(RhinoDoc doc,RhinoObject[] targets,MappingSettings settings,bool force)
    {
        settings.Validate();double scale=UnitScale(doc);var plan=new UvPlan();
        try
        {
            foreach(var obj in targets)
            {
                string backup=Backup(obj);var record=ReadUv(obj);
                if(!force&&UvValid(doc,obj)){plan.Items.Add(new(obj,null,record!,backup));continue;}
                // A recorded projection survives material changes. Only an explicit UV command changes it.
                var chosen=force?settings:record?.Settings??settings;
                if(chosen.Mode is "xatlas" or "tube")throw new InvalidOperationException("展开记录已失效，请先重新执行 xatlas 或沿中心线展开，再应用材质。");
                var (map,mode)=BuildMapping(obj,new MaterialAsset{WidthMeters=1,HeightMeters=1},chosen,scale);
                plan.Items.Add(new(obj,map,new WorldUvRecord{UnitScale=scale,GeometryCrc=obj.Geometry.DataCRC(0),Mode=mode,Settings=MaterialLibrary.Clone(chosen)},backup));
            }
            return plan;
        }
        catch{plan.Dispose();throw;}
    }
    private static void CommitUv(RhinoDoc doc,UvPlan plan)
    {
        foreach(var item in plan.Items)
        {
            var obj=doc.Objects.FindId(item.Object.Id)??throw new InvalidOperationException("物件已删除。");
            if(item.Mapping!=null)
            {
                RemoveUvStorage(obj);obj.SetTextureMapping(1,item.Mapping,Transform.Identity);
                using var actual=obj.GetTextureMapping(1,out var transform);if(actual==null)throw new InvalidOperationException("无法设置真实世界 UV。");
                item.Record.MappingHash=MapHash(actual,transform);item.Record.GeometryCrc=obj.Geometry.DataCRC(0);
            }
            var attrs=obj.Attributes.Duplicate();attrs.SetUserString(BackupKey,item.Backup);attrs.SetUserString(WorldUvKey,Serialize(item.Record));
            if(!doc.Objects.ModifyAttributes(obj.Id,attrs,true))throw new InvalidOperationException("无法保存真实世界 UV。");UvRenderProvider.Refresh(doc,doc.Objects.FindId(obj.Id)!);
        }
    }
    public static object PrepareWorldUv(RhinoDoc doc,Guid[]? objects,Guid[]? layers,MappingSettings settings,bool force=false,bool preview=false)
    {
        using var plan=PlanUv(doc,Targets(doc,objects,layers),settings,force);
        var report=new{computed=plan.Items.Count(i=>i.Mapping!=null),reused=plan.Items.Count(i=>i.Mapping==null),metersPerUv=1,preview,
            objects=plan.Items.Select(i=>new{id=i.Object.Id,mode=i.Record.Mode,reused=i.Mapping==null}).ToArray()};
        if(preview)return report;
        uint undo=doc.BeginUndoRecord("SceneFlow 计算真实世界 UV");
        try{CommitUv(doc,plan);}finally{if(undo!=0)doc.EndUndoRecord(undo);}
        doc.Views.Redraw();return report;
    }
}

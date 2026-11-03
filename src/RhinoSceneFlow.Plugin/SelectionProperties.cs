using Rhino;
using Rhino.DocObjects;
using Rhino.Render;

namespace RhinoSceneFlow.Plugin;

public static class SelectionProperties
{
    private static RhinoObject[] Targets(RhinoDoc doc,Guid[] ids)
    {
        NamedViewExportService.RequireActive(doc);if(ids.Length==0)throw new ArgumentException("先选择物件。");
        return ids.Distinct().Select(id=>doc.Objects.FindId(id)??throw new ArgumentException("物件已删除。")).Select(o=>PlantService.IsPlant(o)?throw new ArgumentException("植物请使用植物属性。"):o).ToArray();
    }
    internal static string Identity(RhinoObject o)=>o.GetRenderMaterial(true)?.Id.ToString()??"classic:"+(o.Attributes.MaterialSource==ObjectMaterialSource.MaterialFromLayer?o.Document.Layers[o.Attributes.LayerIndex].RenderMaterialIndex:o.Attributes.MaterialIndex);
    internal static Guid[] Affected(RhinoDoc doc,Guid[] ids,string scope)
    {
        var selected=Targets(doc,ids);if(scope=="object")return ids;var layers=selected.Select(o=>o.Attributes.LayerIndex).ToHashSet();var materials=selected.Select(Identity).ToHashSet();
        return doc.Objects.GetObjectList(new ObjectEnumeratorSettings{NormalObjects=true,LockedObjects=true,HiddenObjects=true}).Where(o=>!PlantService.IsPlant(o)&&(scope=="layer"?layers.Contains(o.Attributes.LayerIndex):materials.Contains(Identity(o)))).Select(o=>o.Id).ToArray();
    }
    public static object Inspect(RhinoDoc doc,Guid[] ids)=>new{objects=Targets(doc,ids).Select(o=>
    {
        var rm=o.GetRenderMaterial(true);using var m=rm!=null?new Material(rm.ToMaterial(RenderTexture.TextureGeneration.Allow)):new Material(o.GetMaterial(true));
        return new{id=o.Id,name=o.Name,material=Identity(o),materialName=rm?.Name??m.Name,roughness=m.IsPhysicallyBased?m.PhysicallyBased.Roughness:0,metallic=m.IsPhysicallyBased?m.PhysicallyBased.Metallic:0,uv=MaterialService.InspectWorldUv(doc,[o.Id])};
    }).ToArray()};
    public static object Modify(RhinoDoc doc,Guid[] ids,string scope="material",string? name=null,double? roughness=null,double? metallic=null,double? widthMeters=null,double? heightMeters=null)
    {
        var selected=Targets(doc,ids);if(scope is not ("material" or "layer" or "object"))throw new ArgumentException("scope: material | layer | object");
        if(new[]{roughness,metallic}.Any(v=>v.HasValue&&(!double.IsFinite(v.Value)||v<0||v>1))||new[]{widthMeters,heightMeters}.Any(v=>v.HasValue&&(!double.IsFinite(v.Value)||v<=0||v>1e8))||name?.Length>200)throw new ArgumentException("材质参数无效。");
        var all=doc.Objects.GetObjectList(new ObjectEnumeratorSettings{NormalObjects=true,LockedObjects=true,HiddenObjects=true}).Where(o=>!PlantService.IsPlant(o)).ToArray();
        var layerIndices=selected.Select(o=>o.Attributes.LayerIndex).ToHashSet();var identities=selected.Select(Identity).ToHashSet();
        var targets=scope=="layer"?all.Where(o=>layerIndices.Contains(o.Attributes.LayerIndex)).ToArray():scope=="material"?all.Where(o=>identities.Contains(Identity(o))).ToArray():selected;
        if(targets.Any(o=>o.IsLocked))throw new ArgumentException("目标包含锁定物件，请先解锁。");
        var changes=new List<(RhinoObject[] Objects,RenderMaterial Original,RenderMaterial Copy,bool Clone)>();
        try
        {
            foreach(var group in targets.GroupBy(o=>scope=="layer"?o.Attributes.LayerIndex.ToString():Identity(o)))
            {
                var objects=group.ToArray();var source=scope=="layer"?selected.First(o=>o.Attributes.LayerIndex==objects[0].Attributes.LayerIndex):objects[0];var original=source.GetRenderMaterial(true)??throw new ArgumentException("此材质尚无原生渲染材质，请先通过材质库应用材质。");
                if(roughness.HasValue&&original.GetParameter("pbr-roughness")==null||metallic.HasValue&&original.GetParameter("pbr-metallic")==null)throw new ArgumentException("该渲染器材质不支持 PBR 参数，请在原生材质编辑器中修改。");
                bool outside=all.Any(o=>Identity(o)==Identity(source)&&!targets.Any(t=>t.Id==o.Id));
                bool otherLayer=doc.Layers.Any(l=>!l.IsDeleted&&l.RenderMaterial?.Id==original.Id&&(scope!="layer"||!layerIndices.Contains(l.Index)));
                bool clone=scope!="material"&&(outside||otherLayer);
                var copy=(RenderMaterial)original.MakeCopy();changes.Add((objects,original,copy,clone));
                if(name!=null)copy.Name=name;else if(clone)copy.Name=original.Name+" · "+(scope=="object"?"物体":"图层");
                if(roughness.HasValue&&!copy.SetParameter("pbr-roughness",roughness.Value))throw new ArgumentException("无法修改粗糙度。");
                if(metallic.HasValue&&!copy.SetParameter("pbr-metallic",metallic.Value))throw new ArgumentException("无法修改金属度。");
                if(widthMeters.HasValue||heightMeters.HasValue)
                    foreach(var usage in new[]{RenderMaterial.StandardChildSlots.PbrBaseColor,RenderMaterial.StandardChildSlots.PbrRoughness,RenderMaterial.StandardChildSlots.PbrMetallic,RenderMaterial.StandardChildSlots.Bump})
                    {var texture=copy.GetTextureFromUsage(usage);if(texture==null)continue;var repeat=texture.GetRepeat();texture.SetRepeatLocked(false,RenderContent.ChangeContexts.Program);texture.SetRepeat(new(widthMeters.HasValue?1/widthMeters.Value:repeat.X,heightMeters.HasValue?1/heightMeters.Value:repeat.Y,repeat.Z),RenderContent.ChangeContexts.Program);}
            }
            uint undo=doc.BeginUndoRecord("修改选择的材质属性");try
            {
                using var contentUndo=new ContentUndoHelper(doc);
                foreach(var change in changes)
                {
                    var material=change.Original;
                    if(change.Clone){if(!doc.RenderMaterials.Add(change.Copy))throw new InvalidOperationException("无法创建独立材质。");contentUndo.AddContent(change.Copy,null);material=change.Copy;}
                    else
                    {
                        if(!contentUndo.ModifyContent(material))throw new InvalidOperationException("无法记录材质撤销。");
                        material.BeginChange(RenderContent.ChangeContexts.Program);try
                        {if(name!=null)material.Name=name;if(roughness.HasValue)material.SetParameter("pbr-roughness",roughness.Value);if(metallic.HasValue)material.SetParameter("pbr-metallic",metallic.Value);
                         foreach(var usage in new[]{RenderMaterial.StandardChildSlots.PbrBaseColor,RenderMaterial.StandardChildSlots.PbrRoughness,RenderMaterial.StandardChildSlots.PbrMetallic,RenderMaterial.StandardChildSlots.Bump}){var source=change.Copy.GetTextureFromUsage(usage);var target=material.GetTextureFromUsage(usage);if(source!=null&&target!=null&&(widthMeters.HasValue||heightMeters.HasValue)){target.SetRepeatLocked(false,RenderContent.ChangeContexts.Program);target.SetRepeat(source.GetRepeat(),RenderContent.ChangeContexts.Program);}}}
                        finally{material.EndChange();}
                    }
                    if(scope=="layer")foreach(int index in change.Objects.Select(o=>o.Attributes.LayerIndex).Distinct())
                    {var layer=doc.Layers[index];layer.RenderMaterial=material;}
                    if(change.Clone||scope=="layer")foreach(var obj in change.Objects)
                    {if(scope=="layer"&&obj.Attributes.MaterialSource==ObjectMaterialSource.MaterialFromLayer)continue;obj.RenderMaterial=material;obj.CommitChanges();}
                }
            }finally{if(undo!=0)doc.EndUndoRecord(undo);}
            doc.Modified=true;doc.Views.Redraw();return new{scope,objects=targets.Select(o=>o.Id).ToArray(),cloned=changes.Count(c=>c.Clone)};
        }
        finally{foreach(var change in changes)if(!change.Clone||change.Copy.DocumentOwner==null)change.Copy.Dispose();}
    }
}

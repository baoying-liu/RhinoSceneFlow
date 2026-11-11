using Rhino;
using Rhino.Render;
using Rhino.DocObjects;
using RhinoSceneFlow.Core;
namespace RhinoSceneFlow.Plugin;

/// <summary>UI-thread RDK appearance override; snapshots and restores exact child parameters.</summary>
internal sealed class SeasonalMaterials:IDisposable
{
    internal static void ApplyLive(RhinoDoc doc,string season,Guid? asset=null){using var change=new SeasonalMaterials(doc,season,asset);change.restore.Clear();}
    private readonly RhinoDoc doc;private readonly bool modified,recording;
    private readonly List<(RenderTexture Texture,object Filename)> restore=[];
    internal SeasonalMaterials(RhinoDoc doc,string season,Guid? onlyAsset=null)
    {
        this.doc=doc;modified=doc.Modified;recording=doc.UndoRecordingEnabled;doc.UndoRecordingEnabled=false;
        try
        {
            var seen=new HashSet<Guid>();var assets=new Dictionary<Guid,MaterialAsset>();
            foreach(var obj in doc.Objects.GetObjectList(new ObjectEnumeratorSettings{NormalObjects=true,LockedObjects=true,HiddenObjects=false}))
            {
                string? binding=obj.Attributes.MaterialSource==ObjectMaterialSource.MaterialFromLayer?doc.Layers[obj.Attributes.LayerIndex].GetUserString(MaterialService.BindingKey):obj.Attributes.GetUserString(MaterialService.BindingKey);if(binding==null||PlantService.IsPlant(obj))continue;
                var b=MaterialService.Deserialize<MaterialBinding>(binding);if(b.Settings.Checker||onlyAsset.HasValue&&onlyAsset.Value!=b.Asset)continue;if(!assets.TryGetValue(b.Asset,out var asset))assets[b.Asset]=asset=MaterialService.Library.Get(b.Asset);
                string slot=Seasons.Slot(asset,season);if(!asset.Seasonal.Variants.Values.Any(v=>v.Elevation!=null&&v.Elevation!="baseColor"))continue;
                var render=obj.GetRenderMaterial(true);if(render==null||!seen.Add(render.Id))continue;var texture=render.GetTextureFromUsage(RenderMaterial.StandardChildSlots.PbrBaseColor);if(texture==null)continue;
                var old=texture.GetParameter("filename");if(old==null)throw new InvalidOperationException("材质颜色纹理没有可恢复的 filename 参数。");
                string selected=RandomTextureService.SeasonalPath(asset,slot,obj.Attributes.MaterialSource==ObjectMaterialSource.MaterialFromLayer?doc.Layers[obj.Attributes.LayerIndex].Id:obj.Id,b.Randomized);
                restore.Add((texture,old));texture.BeginChange(RenderContent.ChangeContexts.Program);try{if(!texture.SetParameter("filename",selected))throw new InvalidOperationException("无法切换材质的季节图片。");}finally{texture.EndChange();}
            }
        }
        catch{Dispose();throw;}
    }
    public void Dispose()
    {
        try{foreach(var (texture,file) in restore){texture.BeginChange(RenderContent.ChangeContexts.Program);try{texture.SetParameter("filename",file);}finally{texture.EndChange();}}restore.Clear();}
        finally{doc.Modified=modified;doc.UndoRecordingEnabled=recording;}
    }
}

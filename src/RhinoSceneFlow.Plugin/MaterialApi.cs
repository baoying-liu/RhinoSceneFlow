using System.Text.Json;
using Rhino;
using RhinoSceneFlow.Core;

namespace RhinoSceneFlow.Plugin;

internal static class MaterialApi
{
    internal static object Contract=>new{operations=new[]{"material_prepare_uv","material_uv_status","material_quick_open","material_quick_status","material_generation_progress","material_library","material_configure","material_import","material_update","material_apply","material_preview","material_restore","material_inspect","material_remap","material_pack","material_unpack","material_generation_request","material_generation_jobs","material_generation_complete","material_generation_cancel","material_open_panel","material_panel_status"},
        units="Asset widthMeters/heightMeters and mapping origin/offsets are meters; converted to document units. Channel 1, persistent backup. Whole layers or object IDs, not both.",
        generation="Agent workflow: request -> list pending jobs -> generate image using connected provider -> complete with local files. No embedded API provider or automatic generation claim.",
        imageMaps=new[]{"baseColor","roughness","normal","metallic"}};
    private static T Read<T>(JsonElement r,string key)=>JsonSerializer.Deserialize<T>(r.GetProperty(key).GetRawText(),MaterialLibrary.Json)??throw new ArgumentException("缺少参数："+key);
    private static Guid Id(JsonElement r,string key="assetId")=>Guid.Parse(r.GetProperty(key).GetString()!);
    private static Guid[]? Ids(JsonElement r,string key)=>r.TryGetProperty(key,out var a)?a.EnumerateArray().Select(v=>Guid.Parse(v.GetString()!)).ToArray():null;
    private static RhinoDoc Doc(JsonElement r)=>RhinoDoc.FromRuntimeSerialNumber(r.GetProperty("document").GetUInt32())??throw new ArgumentException("文档已关闭。");
    private static MappingSettings Mapping(JsonElement r)=>r.TryGetProperty("mapping",out var m)?JsonSerializer.Deserialize<MappingSettings>(m.GetRawText(),MaterialLibrary.Json)!:new();
    internal static object Execute(string operation,JsonElement r)=>operation switch
    {
        "material_prepare_uv"=>MaterialService.PrepareWorldUv(Doc(r),Ids(r,"objects"),Ids(r,"layers"),Mapping(r),r.TryGetProperty("force",out var force)&&force.GetBoolean(),r.TryGetProperty("preview",out var preview)&&preview.GetBoolean()),
        "material_uv_status"=>MaterialService.InspectWorldUv(Doc(r),Ids(r,"objects")??throw new ArgumentException("需要 objects。")),
        "material_quick_open"=>MaterialQuickController.Open(Doc(r),Ids(r,"objects")).GetState(),
        "material_quick_status"=>MaterialQuickController.Find(Doc(r).RuntimeSerialNumber)?.GetState()??new{open=false},
        "material_generation_progress"=>MaterialGeneration.Progress(Id(r,"jobId"),r.GetProperty("stage").GetString()!),
        "material_library"=>new{directory=MaterialService.Library.Root,assets=MaterialService.Library.List(r.TryGetProperty("query",out var q)?q.GetString()??"":""),contract=Contract},
        "material_configure"=>Configure(r.GetProperty("directory").GetString()!),
        "material_import"=>MaterialService.Import(Read<MaterialAsset>(r,"asset"),Read<Dictionary<string,string>>(r,"files")),
        "material_update"=>MaterialService.Library.Update(Read<MaterialAsset>(r,"asset")),
        "material_apply"=>MaterialService.Apply(Doc(r),Id(r),Ids(r,"objects"),Ids(r,"layers"),Mapping(r)),
        "material_preview"=>MaterialService.Apply(Doc(r),Id(r),Ids(r,"objects"),Ids(r,"layers"),Mapping(r),true),
        "material_restore"=>MaterialService.Restore(Doc(r),Ids(r,"objects"),Ids(r,"layers")),
        "material_inspect"=>MaterialService.Inspect(Doc(r),Ids(r,"objects")??throw new ArgumentException("需要 objects。")),
        "material_remap"=>r.TryGetProperty("layers",out _)?MaterialService.SyncLayers(Doc(r),Ids(r,"layers")!):MaterialService.Remap(Doc(r),Ids(r,"objects")??throw new ArgumentException("需要 objects 或 layers。")),
        "material_pack"=>Pack(Id(r),r.GetProperty("path").GetString()!),
        "material_unpack"=>MaterialService.Library.ImportPackage(r.GetProperty("path").GetString()!,MaterialService.ValidateImages),
        "material_generation_request"=>MaterialGeneration.Request(Read<MaterialAsset>(r,"asset"),r.GetProperty("prompt").GetString()!,r.TryGetProperty("referenceImages",out var refs)?refs.EnumerateArray().Select(v=>v.GetString()!).ToArray():null),
        "material_generation_jobs"=>MaterialGeneration.List(),
        "material_generation_complete"=>MaterialGeneration.Complete(Id(r,"jobId"),Read<Dictionary<string,string>>(r,"files")),
        "material_generation_cancel"=>MaterialGeneration.Cancel(Id(r,"jobId")),
        "material_open_panel"=>MaterialPanelController.Open(Doc(r)).GetState(),
        "material_panel_status"=>MaterialPanelController.Find(Doc(r).RuntimeSerialNumber)?.GetState()??new{open=false},
        _=>throw new ArgumentException("未知材质操作。")
    };
    private static object Configure(string directory){SceneFlowPlugin.Instance.MaterialDirectory=directory;return new{directory=MaterialService.Library.Root};}
    private static object Pack(Guid id,string path){MaterialService.Library.ExportPackage(id,path);return new{path};}
}

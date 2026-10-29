using System.Text.Json;
using Rhino;
using RhinoSceneFlow.Core;

namespace RhinoSceneFlow.Plugin;

internal static class MaterialApi
{
    internal static object Contract=>new{operations=new[]{"material_random_settings","material_random_prepare","material_random_status","material_random_cancel","material_workspace_group","material_tool_settings","material_update_labels","material_workspace_open","material_workspace_status","material_shelf_open","material_tool_select","material_tool_apply","material_catalog_organize","material_catalog_status","material_catalog_cancel","material_native_preview","material_uv_renderer","material_chat_start","material_chat_status","material_chat_cancel","material_unwrap_start","material_unwrap_status","material_unwrap_cancel","material_generation_start","material_generation_executor","material_prepare_uv","material_uv_status","material_quick_open","material_quick_status","material_generation_progress","material_library","material_configure","material_import","material_update","material_apply","material_preview","material_restore","material_inspect","material_remap","material_pack","material_unpack","material_generation_request","material_generation_jobs","material_generation_complete","material_generation_cancel","material_open_panel","material_panel_status"},
        units="Asset widthMeters/heightMeters and mapping origin/offsets are meters; converted to document units. Channel 1, persistent backup. Whole layers or object IDs, not both.",
        generation="material_generation_start runs local Codex image generation using existing ChatGPT login and imports a fresh PNG automatically. material_generation_request retains manual Agent handoff. Terminal states: completed, failed, cancelled.",
        imageMaps=new[]{"baseColor","roughness","normal","metallic"}};
    private static T Read<T>(JsonElement r,string key)=>JsonSerializer.Deserialize<T>(r.GetProperty(key).GetRawText(),MaterialLibrary.Json)??throw new ArgumentException("缺少参数："+key);
    private static Guid Id(JsonElement r,string key="assetId")=>Guid.Parse(r.GetProperty(key).GetString()!);
    private static Guid[]? Ids(JsonElement r,string key)=>r.TryGetProperty(key,out var a)?a.EnumerateArray().Select(v=>Guid.Parse(v.GetString()!)).ToArray():null;
    private static RhinoDoc Doc(JsonElement r)=>RhinoDoc.FromRuntimeSerialNumber(r.GetProperty("document").GetUInt32())??throw new ArgumentException("文档已关闭。");
    private static MappingSettings Mapping(JsonElement r)=>r.TryGetProperty("mapping",out var m)?JsonSerializer.Deserialize<MappingSettings>(m.GetRawText(),MaterialLibrary.Json)!:new();
    internal static object Execute(string operation,JsonElement r)=>operation switch
    {
        "material_random_prepare"=>RandomTextureService.Start(Doc(r),Id(r),Ids(r,"objects"),Ids(r,"layers"),r.TryGetProperty("preview",out var rp)?rp.GetBoolean():!r.TryGetProperty("objects",out _)&&!r.TryGetProperty("layers",out _)),
        "material_random_status"=>RandomTextureService.Get(Id(r,"jobId")),
        "material_random_cancel"=>RandomTextureService.Cancel(Id(r,"jobId")),
        "material_random_settings"=>RandomSettings(r),
        "material_uv_renderer"=>r.TryGetProperty("objectId",out _)?UvRenderProvider.Inspect(Doc(r),Id(r,"objectId")):UvRenderProvider.Status(),
        "material_workspace_open"=>SceneFlowWorkspace.Open(r.TryGetProperty("page",out var page)?page.GetString()!:"materials"),
        "material_workspace_status"=>SceneFlowWorkspace.State(),
        "material_workspace_group"=>SceneFlowWorkspace.Group(),
        "material_shelf_open"=>Shelf(r),
        "material_tool_select"=>Select(r),
        "material_tool_apply"=>ApplyTool(r),
        "material_tool_settings"=>SettingsTool(r),
        "material_catalog_organize"=>CatalogService.Organize(),
        "material_catalog_status"=>CatalogService.Get(Id(r,"jobId")),
        "material_catalog_cancel"=>CatalogService.Cancel(Id(r,"jobId")),
        "material_native_preview"=>Preview(r),
        "material_chat_start"=>MaterialChat.Start(r.GetProperty("conversation").GetString()!,r.TryGetProperty("referenceImages",out var chatRefs)?chatRefs.EnumerateArray().Select(v=>v.GetString()!).ToArray():[],r.TryGetProperty("widthMeters",out var cw)?cw.GetDouble():1,r.TryGetProperty("heightMeters",out var ch)?ch.GetDouble():1,!r.TryGetProperty("reuseSimilar",out var reuse)||reuse.GetBoolean()),
        "material_chat_status"=>MaterialChat.Get(Id(r,"jobId")),
        "material_chat_cancel"=>MaterialChat.Cancel(Id(r,"jobId")),
        "material_unwrap_start"=>UnwrapService.Start(Doc(r),Ids(r,"objects"),Ids(r,"layers"),r.TryGetProperty("method",out var unwrapMethod)?unwrapMethod.GetString()!:"xatlas",r.TryGetProperty("guideId",out _)?Id(r,"guideId"):null),
        "material_unwrap_status"=>UnwrapService.Get(Id(r,"jobId")),
        "material_unwrap_cancel"=>UnwrapService.Cancel(Id(r,"jobId")),
        "material_prepare_uv"=>MaterialService.PrepareWorldUv(Doc(r),Ids(r,"objects"),Ids(r,"layers"),Mapping(r),r.TryGetProperty("force",out var force)&&force.GetBoolean(),r.TryGetProperty("preview",out var preview)&&preview.GetBoolean()),
        "material_uv_status"=>MaterialService.InspectWorldUv(Doc(r),Ids(r,"objects")??throw new ArgumentException("需要 objects。")),
        "material_quick_open"=>SceneFlowWorkspace.Open("materials"),
        "material_quick_status"=>SceneFlowWorkspace.Materials?.GetState()??new{open=false},
        "material_generation_progress"=>MaterialGeneration.Progress(Id(r,"jobId"),r.GetProperty("stage").GetString()!),
        "material_library"=>new{directory=MaterialService.Library.Root,assets=MaterialCatalog.Filter(MaterialService.Library.List(),r.TryGetProperty("query",out var q)?q.GetString()??"":"",r.TryGetProperty("category",out var cat)?cat.GetString()??"":"",r.TryGetProperty("tag",out var tag)?tag.GetString()??"":""),contract=Contract},
        "material_configure"=>Configure(r.GetProperty("directory").GetString()!),
        "material_import"=>MaterialService.Import(Read<MaterialAsset>(r,"asset"),Read<Dictionary<string,string>>(r,"files")),
        "material_update"=>MaterialService.Library.Update(Read<MaterialAsset>(r,"asset")),
        "material_update_labels"=>MaterialService.Library.UpdateLabels(Id(r),r.GetProperty("name").GetString()!,r.GetProperty("category").GetString()!,Read<string[]>(r,"tags"),r.TryGetProperty("expectedCatalogRevision",out var expected)?expected.GetInt32():null),
        "material_apply"=>MaterialService.Apply(Doc(r),Id(r),Ids(r,"objects"),Ids(r,"layers"),Mapping(r)),
        "material_preview"=>MaterialService.Apply(Doc(r),Id(r),Ids(r,"objects"),Ids(r,"layers"),Mapping(r),true),
        "material_restore"=>MaterialService.Restore(Doc(r),Ids(r,"objects"),Ids(r,"layers")),
        "material_inspect"=>MaterialService.Inspect(Doc(r),Ids(r,"objects")??throw new ArgumentException("需要 objects。")),
        "material_remap"=>r.TryGetProperty("layers",out _)?MaterialService.SyncLayers(Doc(r),Ids(r,"layers")!):MaterialService.Remap(Doc(r),Ids(r,"objects")??throw new ArgumentException("需要 objects 或 layers。")),
        "material_pack"=>Pack(Id(r),r.GetProperty("path").GetString()!),
        "material_unpack"=>MaterialService.Library.ImportPackage(r.GetProperty("path").GetString()!,MaterialService.ValidateImages),
        "material_generation_executor"=>MaterialGeneration.ExecutorStatus(),
        "material_generation_start"=>MaterialGeneration.Start(Read<MaterialAsset>(r,"asset"),r.GetProperty("prompt").GetString()!,r.TryGetProperty("referenceImages",out var startRefs)?startRefs.EnumerateArray().Select(v=>v.GetString()!).ToArray():null),
        "material_generation_request"=>MaterialGeneration.Request(Read<MaterialAsset>(r,"asset"),r.GetProperty("prompt").GetString()!,r.TryGetProperty("referenceImages",out var refs)?refs.EnumerateArray().Select(v=>v.GetString()!).ToArray():null),
        "material_generation_jobs"=>MaterialGeneration.List(),
        "material_generation_complete"=>MaterialGeneration.Complete(Id(r,"jobId"),Read<Dictionary<string,string>>(r,"files")),
        "material_generation_cancel"=>MaterialGeneration.Cancel(Id(r,"jobId")),
        "material_open_panel"=>Shelf(r),
        "material_panel_status"=>SceneFlowWorkspace.Library?.GetState()??new{open=false},
        _=>throw new ArgumentException("未知材质操作。")
    };
    private static object Shelf(JsonElement r){bool visible=!r.TryGetProperty("visible",out var v)||v.GetBoolean();SceneFlowWorkspace.Open(visible?"library":"materials");return (visible?SceneFlowWorkspace.Library:SceneFlowWorkspace.Materials)!.GetState();}
    private static MaterialsTool Tool(JsonElement r){string page=r.TryGetProperty("page",out var p)?p.GetString()!:"materials";if(page is not ("materials" or "library"))throw new ArgumentException("page: materials | library");SceneFlowWorkspace.Open(page);return (page=="library"?SceneFlowWorkspace.Library:SceneFlowWorkspace.Materials)??throw new ArgumentException("材质工具不可用。");}
    private static object Select(JsonElement r){var tool=Tool(r);tool.SelectAsset(Id(r));return tool.GetState();}
    private static object ApplyTool(JsonElement r){var doc=Doc(r);NamedViewExportService.RequireActive(doc);var tool=Tool(r);if(tool.DocumentSerial!=doc.RuntimeSerialNumber)throw new ArgumentException("工具尚未切换到当前文档，请重新打开材质工具。");tool.Apply();return tool.GetState();}
    private static object SettingsTool(JsonElement r){var tool=Tool(r);tool.Configure(r.TryGetProperty("reuseSimilar",out var reuse)?reuse.GetBoolean():null,r.TryGetProperty("scope",out var scope)?scope.GetString():null);return tool.GetState();}
    private static object Preview(JsonElement r){string path=Path.GetFullPath(r.GetProperty("path").GetString()!);if(!Path.IsPathFullyQualified(r.GetProperty("path").GetString()!)||!path.EndsWith(".png",StringComparison.OrdinalIgnoreCase))throw new ArgumentException("需要绝对 PNG 路径。");Directory.CreateDirectory(Path.GetDirectoryName(path)!);using var b=NativeMaterialPreview.Render(MaterialService.Library.Get(Id(r)));b.Save(path,System.Drawing.Imaging.ImageFormat.Png);return new{path};}
    private static object Configure(string directory){SceneFlowPlugin.Instance.MaterialDirectory=directory;return new{directory=MaterialService.Library.Root};}
    private static object RandomSettings(JsonElement r)
    {
        var a=MaterialService.Library.Get(Id(r));
        if(r.TryGetProperty("expectedRevision",out var expected)&&expected.GetInt32()!=a.Revision)throw new InvalidOperationException("材质已更新，请重新读取。");
        if(r.TryGetProperty("expectedCatalogRevision",out var catalog)&&catalog.GetInt32()!=a.CatalogRevision)throw new InvalidOperationException("材质属性已更新，请重新读取。");
        a.Randomization=Read<TextureRandomization>(r,"settings");return MaterialService.Library.Update(a);
    }
    private static object Pack(Guid id,string path){MaterialService.Library.ExportPackage(id,path);return new{path};}
}

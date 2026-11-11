using RhinoSceneFlow.Core;
using System.Text.Json;
using System.Text.Json.Nodes;
using Rhino;
using Rhino.PlugIns;

namespace RhinoSceneFlow.Plugin;

/// <summary>Called through the installed Rhino-MCP-Platform run_python tool, never a second server.</summary>
public static class McpApi
{
    private static readonly Guid PlatformId = new("2668d7ed-f507-4a68-8295-8172147a0e39");
    private static readonly JsonSerializerOptions Json = new() { PropertyNamingPolicy = JsonNamingPolicy.CamelCase };

    public static string Execute(string requestJson)
    {
        try
        {
            if (RhinoApp.InvokeRequired) throw new ApiException("wrong_thread", "Call through Rhino-MCP-Platform on Rhino's UI thread.");
            if (PlugIn.Find(PlatformId) is null) throw new ApiException("platform_unavailable", "Rhino-MCP-Platform must be loaded.");
            if (requestJson is null || requestJson.Length > 65536) throw new ArgumentException("Request limit: 64 KiB.");
            using var parsed = JsonDocument.Parse(requestJson);
            var r = parsed.RootElement;
            if (r.GetProperty("apiVersion").GetInt32() != 1) throw new ApiException("unsupported_version", "Use apiVersion=1.");
            string operation = r.GetProperty("operation").GetString() ?? "";
            object response;
            switch (operation)
            {
                case "plugin_settings":
                    response=r.TryGetProperty("settings",out var preferences)?PluginPreferences.Save(JsonSerializer.Deserialize<PluginPreferences>(preferences.GetRawText(),MaterialLibrary.Json)!):PluginPreferences.Load();break;
                case "plugin_settings_open":PluginPreferences.Show();response=new{closed=true};break;
                case "seasonal_start":response=SeasonalGeneration.Start(Guid.Parse(r.GetProperty("assetId").GetString()!),r.TryGetProperty("plant",out var isPlant)&&isPlant.GetBoolean(),!r.TryGetProperty("fourSeasons",out var four)||four.GetBoolean());break;
                case "seasonal_status":response=SeasonalGeneration.Status(Guid.Parse(r.GetProperty("jobId").GetString()!));break;
                case "seasonal_cancel":response=SeasonalGeneration.Cancel(Guid.Parse(r.GetProperty("jobId").GetString()!));break;
                case "seasonal_asset":
                    var seasonalLibrary=r.TryGetProperty("plant",out var plantAsset)&&plantAsset.GetBoolean()?PlantService.Library:MaterialService.Library;
                    var seasonalAsset=seasonalLibrary.Get(Guid.Parse(r.GetProperty("assetId").GetString()!));
                    if(r.TryGetProperty("seasonal",out var seasonalSettings)){seasonalAsset.Seasonal=JsonSerializer.Deserialize<SeasonalAppearance>(seasonalSettings.GetRawText(),MaterialLibrary.Json)!;seasonalAsset=seasonalLibrary.Update(seasonalAsset);PlantService.RefreshSeasons();}response=seasonalAsset;break;
                case "workbench_activate":var activateDoc=Document(r);WorkbenchService.Activate(activateDoc,WorkbenchService.Settings(activateDoc).First(v=>v.Id==Guid.Parse(r.GetProperty("viewId").GetString()!)));response=new{activated=true};break;
                case "postproduction_start":
                    response=PostProduction.Start(Document(r),r.TryGetProperty("path",out var postPath)?postPath.GetString():null,r.TryGetProperty("browser",out var postBrowser)&&postBrowser.GetBoolean());break;
                case "postproduction_status":
                    response=PostProduction.Get(Guid.Parse(r.GetProperty("jobId").GetString()!));break;
                case "postproduction_request":
                    response=PostProduction.Request(r.GetProperty("route").GetString()!,r.TryGetProperty("method",out var postMethod)?postMethod.GetString()!:"GET",r.TryGetProperty("body",out var postBody)?postBody.GetRawText():null);break;
                case "selection_properties":
                    response=SelectionProperties.Inspect(Document(r),r.GetProperty("objects").EnumerateArray().Select(v=>Guid.Parse(v.GetString()!)).ToArray());break;
                case "selection_material_update":
                    response=SelectionProperties.Modify(Document(r),r.GetProperty("objects").EnumerateArray().Select(v=>Guid.Parse(v.GetString()!)).ToArray(),r.TryGetProperty("scope",out var ps)?ps.GetString()!:"material",r.TryGetProperty("name",out var pn)?pn.GetString():null,r.TryGetProperty("roughness",out var pr)?pr.GetDouble():null,r.TryGetProperty("metallic",out var pm)?pm.GetDouble():null,r.TryGetProperty("widthMeters",out var pw)?pw.GetDouble():null,r.TryGetProperty("heightMeters",out var ph)?ph.GetDouble():null);break;
                case "describe":
                    response = new { name = "RhinoSceneFlow", version = typeof(McpApi).Assembly.GetName().Version!.ToString(3), transport = "Rhino-MCP-Platform.run_python",materialLibrary=MaterialApi.Contract,plants=PlantApi.Operations,
                        entryPoint = "RhinoSceneFlow.Plugin.McpApi.Execute(string)",
                        operations = new object[] {
                            new {name="plugin_settings",required=Array.Empty<string>(),parameters="settings?: language:auto|zh|en, theme:rhino|light|dark, season:spring|summer|autumn|winter, climate, generateFourSeasons; plugin_settings_open opens native settings",output="Preferences"},
                            new {name="seasonal_start",required=new[]{"assetId"},parameters="plant?:false, fourSeasons?:true; only missing variants, summer elevation+plan for plants; seasonal_status/seasonal_cancel require jobId; successful slots persist on cancellation",output="Seasonal job"},
                            new {name="seasonal_asset",required=new[]{"assetId"},parameters="plant?:false, seasonal?: followSeason/fixedSeason/climate/variants; returns single parent library record",output="Asset"},
                            new {name="workbench_activate",required=new[]{"document","viewId"},parameters="Activates Named View and its preview season/mode without entering detail editor; configure_view supports previewSeason/followPreviewSeason/exportSeasons/seasonExpanded",output="activated"},
                            new {name="postproduction_start",required=new[]{"document"},parameters="path?: absolute PSD/PSB; browser?:false(default); starts/reuses authenticated local Web workbench; file snapshot and current-document metadata only",output="Launch job id; poll postproduction_status. Completed launch is not completed PSD parsing."},
                            new {name="postproduction_status",required=new[]{"jobId"},parameters="Launch/request job GUID",output="status,stage,url (contains local bearer fragment; do not log),project,importJob,response,error. PNG generation/fusion jobs have their own HTTP job/run IDs."},
                            new {name="postproduction_request",required=new[]{"route"},parameters="Authenticated JSON-only Web request via original Platform. route:/api/status|projects/...|jobs/...; method:GET(default)|POST|PUT; body?:JSON. Supports generate, resume, review acceptance, retry, cancel, run/settings/status; no second MCP server.",output="Request job; poll postproduction_status for response, then poll backend image job via this same operation."},
                            new { name="selection_properties",required=new[]{"document","objects"},parameters="objects:[GUID]; effective native materials and world UV status",output="Selected object properties" },
                            new { name="selection_material_update",required=new[]{"document","objects"},parameters="scope:material(default)|layer|object; name?,roughness?,metallic?,widthMeters?,heightMeters?; document-only RDK edits with isolation and Undo; prepare UV through existing UV operations when needed",output="Affected objects and clone count" },
                            new { name="workbench_create_view",required=new[]{"document"},parameters="name?: create a native Named View from the active viewport (auto-numbered if absent)",output="viewId" },
                            new { name="workbench_rename_view",required=new[]{"document","viewId","name"},parameters="Rename the native Named View in place; duplicate/empty names rejected",output="viewId,name" },
                            new { name="workbench_expand",required=new[]{"document","expanded"},parameters="scope:view(default)|layers; viewId?: target one or all cards; independent section folding",output="Panel state" },
                            new { name="workbench_settings",required=new[]{"document"},parameters="Per-view configuration, exportable display modes and PSD blend keys",output="views, displayModes, blends" },
                            new { name="configure_view",required=new[]{"document","viewId","settings"},parameters="Patch width,height,mode,layers:[{kind:shadow|texture|material|display|plants|color|depth,colorSource:material(default)|layer,textureGrouping:material(default)|object|all,plantGrouping:species(default)|individual|all,visible:true,expanded:false,mode:guid,blend:norm|mul |scrn|over|dark|lite,opacity:0..100,enabled:true}], camera:{yaw,pitch,zoom,panX,panY,panZ}, sun:{useDocument,azimuth,altitude},included. Saved per document path, without altering Named Views.",output="Updated view configuration" },
                            new { name="export_workbench",required=new[]{"document","directory"},parameters="views?: [Named View GUIDs] (otherwise included saved views); collision?: number|overwrite|cancel. Captures RGB display modes, unlit bitmap albedo (kind:texture, material-ID merge or per-object children in one group), legacy layer RGB (kind:material), and tiled shadows. Independent pass blend/opacity. Side <=8192; total <=8192 squared; PSD raw <=2GB.",output="Batch report" },
                            new { name="open_panel", required=new[]{"document"}, parameters="Opens or activates the native Eto Named View export panel", output="Panel state" },
                            new { name="panel_status", required=new[]{"document"}, parameters="Read-only panel state", output="Panel state, or open=false" },
                            new { name="named_views", required=new[]{"document"}, parameters="Lists stable named-view IDs and default dimensions", output="Named View entries" },
                            new { name="export_named_views", required=new[]{"document","directory","views"}, parameters="views: [{viewId,width,height}]; channels?: [material,shadow] (material currently layer RGB; shadow includes backlit surfaces, direct sunlight only); collision?: number (default), overwrite, cancel; writes one PSD per Named View", output="Batch files, dimensions, layer counts, timing and per-view errors" },
                            new { name="describe", required=Array.Empty<string>(), parameters="apiVersion=1", output="Version, operation contracts, limitations" },
                            new { name="status", required=new[]{"document"}, parameters="document: Rhino runtime serial number", output="Default directory, document and active viewport" },
                            new { name="configure_export", required=new[]{"directory"}, parameters="directory: absolute path; directory is created on export", output="Persisted default export directory" },
                            new { name="export_shadow_psd", required=new[]{"document"}, parameters="width?, path?, viewportId?, overwrite?; toSun?: [x,y,z] surface-to-sun direction (default enabled Rhino sun or [-1,-1,2]); color?: #RRGGBB (default #5A5A5A); opacity?: (0,1] default 1; includeFormShading?: true for volume, false for legacy ray; bias?: positive model units; backend?: ray (legacy default) or volume (z-fail volumes with original-surface refinement)", output="Export report (including surfaceRefinements query count) plus normalized light direction, source, style, bias, backend and empty flag" },
                            new { name="export_psd", required=new[]{"document"}, parameters="width?: 64..8192 (default 2048), path?: absolute .psd (default generated), viewportId?: expected active viewport GUID, overwrite?: false", output="File path, dimensions, layers, object/triangle counts, skipped types, timing" }
                        }, limits = new { maxPixels=8_000_000, workbenchMaxPixels=67_108_864,maxSide=8192, bitDepth=8, grouping="layer_rgb", appearance="opaque_flat_color_and_display_rgb" } };
                    break;
                case "workbench_settings":
                    response=new{views=WorkbenchService.Settings(Document(r)),displayModes=WorkbenchService.Modes().Select(m=>new{id=m.Id,name=m.LocalName}),blends=Ui.Blends.Select(b=>new{key=b.Key,name=b.Name})};break;
                case "workbench_create_view":
                    var createDoc=Document(r);response=new{viewId=WorkbenchService.CreateNamedView(createDoc,r.TryGetProperty("name",out var createdName)?createdName.GetString():null)};break;
                case "workbench_rename_view":
                    var renameDoc=Document(r);var renameId=Guid.Parse(r.GetProperty("viewId").GetString()!);var renameName=r.GetProperty("name").GetString()!;
                    if(ExportPanelController.Find(renameDoc.RuntimeSerialNumber) is {} renamePanel)renamePanel.RenameView(renameId,renameName);else WorkbenchService.RenameNamedView(renameDoc,renameId,renameName);response=new{viewId=renameId,name=renameName.Trim()};break;
                case "workbench_expand":
                    ExportPanelController.Open(Document(r)).SetExpansion(r.GetProperty("expanded").GetBoolean(),r.TryGetProperty("scope",out var foldScope)?foldScope.GetString()!:"view",r.TryGetProperty("viewId",out var foldId)?Guid.Parse(foldId.GetString()!):null);response=ExportPanelController.Find(Document(r).RuntimeSerialNumber)!.GetState();break;
                case "configure_view":
                    var configDoc=Document(r);var configId=Guid.Parse(r.GetProperty("viewId").GetString()!);
                    var existing=WorkbenchService.Settings(configDoc).FirstOrDefault(v=>v.Id==configId)??throw new ArgumentException("Named View does not exist.");
                    var node=JsonSerializer.SerializeToNode(existing,WorkbenchStore.Json)!.AsObject();
                    Merge(node,JsonNode.Parse(r.GetProperty("settings").GetRawText())!.AsObject());
                    var configured=node.Deserialize<ViewExportRow>(WorkbenchStore.Json)!;configured.Id=configId;
                    WorkbenchService.Configure(configDoc,configured);response=configured;break;
                case "export_workbench":
                    var workDoc=Document(r);var settings=WorkbenchService.Settings(workDoc);
                    if(r.TryGetProperty("views",out var ids))
                    {var selected=ids.EnumerateArray().Select(v=>Guid.Parse(v.GetString()!)).ToArray();if(selected.Distinct().Count()!=selected.Length||selected.Any(id=>settings.All(v=>v.Id!=id)))throw new ArgumentException("Invalid or duplicate Named View ID.");foreach(var view in settings)view.Included=selected.Contains(view.Id);}
                    string workPolicy=r.TryGetProperty("collision",out var workCollision)?workCollision.GetString()??"number":"number";
                    var workAction=workPolicy switch{"number"=>FileCollision.Number,"overwrite"=>FileCollision.Overwrite,"cancel"=>FileCollision.Cancel,_=>throw new ArgumentException("Invalid collision policy.")};
                    var workPlan=WorkbenchService.Plan(workDoc,settings,r.GetProperty("directory").GetString()??"",_=>workAction);
                    response=WorkbenchService.Export(workDoc,workPlan);break;
                case "open_panel":
                    response=ExportPanelController.Open(Document(r)).GetState();break;
                case "panel_status":
                    response=ExportPanelController.Find(Document(r).RuntimeSerialNumber)?.GetState() ?? (object)new {open=false};break;
                case "named_views":
                    response=NamedViewExportService.List(Document(r));break;
                case "export_named_views":
                    var batchDoc=Document(r);
                    var views=r.GetProperty("views").EnumerateArray().Select(v=>new NamedViewSpec(
                        Guid.Parse(v.GetProperty("viewId").GetString()!),v.GetProperty("width").GetInt32(),v.GetProperty("height").GetInt32())).ToArray();
                    string[] channels=r.TryGetProperty("channels",out var channelList)?channelList.EnumerateArray().Select(c=>c.GetString()??"").ToArray():["material","shadow"];
                    if(channels.Any(c=>c is not ("material" or "shadow")))throw new ArgumentException("channels must contain material and/or shadow.");
                    string collision=r.TryGetProperty("collision",out var policy)?policy.GetString()??"number":"number";
                    var action=collision switch {"number"=>FileCollision.Number,"overwrite"=>FileCollision.Overwrite,"cancel"=>FileCollision.Cancel,_=>throw new ArgumentException("collision must be number, overwrite or cancel.")};
                    var passes=new BatchChannels(channels.Contains("material"),channels.Contains("shadow"));
                    var plan=NamedViewExportService.Plan(batchDoc,views,r.GetProperty("directory").GetString()??"",passes,_=>action);
                    response=NamedViewExportService.Export(batchDoc,plan,passes);break;
                case "configure_export":
                    string directory = r.GetProperty("directory").GetString() ?? "";
                    if (!Path.IsPathFullyQualified(directory)) throw new ArgumentException("Directory must be an absolute path.");
                    directory = Path.GetFullPath(directory);
                    if (File.Exists(directory)) throw new ArgumentException("Directory points to an existing file.");
                    SceneFlowPlugin.Instance.ExportDirectory = directory;
                    response = new { directory }; break;
                case "status":
                    var doc = Document(r);
                    var vp = doc.Views.ActiveView?.ActiveViewport;
                    response = new { document=doc.RuntimeSerialNumber, defaultDirectory=SceneFlowPlugin.Instance.ExportDirectory,
                        viewportId=vp?.Id, viewName=vp?.Name, width=vp?.Size.Width, height=vp?.Size.Height,
                        projection=vp is null ? null : vp.IsParallelProjection ? "parallel" : "perspective", platformLoaded=true };
                    break;
                case "export_shadow_psd":
                    Vec3? toSun = null;
                    if (r.TryGetProperty("toSun", out var light))
                    {
                        if (light.GetArrayLength() != 3) throw new ArgumentException("toSun must contain 3 numbers.");
                        toSun = new Vec3(light[0].GetDouble(),light[1].GetDouble(),light[2].GetDouble());
                    }
                    Rgb? shadowColor = null;
                    if (r.TryGetProperty("color", out var rgb))
                    {
                        string hex = rgb.GetString() ?? "";
                        if (hex.Length != 7 || hex[0] != '#') throw new ArgumentException("Color must be #RRGGBB.");
                        shadowColor = new Rgb(Convert.ToByte(hex.Substring(1,2),16),Convert.ToByte(hex.Substring(3,2),16),Convert.ToByte(hex.Substring(5,2),16));
                    }
                    response = ExportService.ExportShadow(Document(r), r.TryGetProperty("width", out var sw) ? sw.GetInt32() : 2048,
                        r.TryGetProperty("path", out var sp) ? sp.GetString() : null,
                        r.TryGetProperty("overwrite", out var so) && so.GetBoolean(),
                        r.TryGetProperty("viewportId", out var sv) ? Guid.Parse(sv.GetString()!) : null,
                        toSun, shadowColor, r.TryGetProperty("opacity", out var opacity) ? opacity.GetDouble() : 1,
                        r.TryGetProperty("includeFormShading", out var form) ? form.GetBoolean() : r.TryGetProperty("backend",out var formBackend) && formBackend.GetString()=="volume",
                        r.TryGetProperty("bias", out var bias) ? bias.GetDouble() : null,
                        r.TryGetProperty("backend", out var backend) ? backend.GetString() ?? "ray" : "ray");
                    break;
                case "export_psd":
                    response = ExportService.Export(Document(r), r.TryGetProperty("width", out var width) ? width.GetInt32() : 2048,
                        r.TryGetProperty("path", out var path) ? path.GetString() : null,
                        r.TryGetProperty("overwrite", out var overwrite) && overwrite.GetBoolean(),
                        r.TryGetProperty("viewportId", out var viewport) ? Guid.Parse(viewport.GetString()!) : null);
                    break;
                default:
                    if(operation.StartsWith("plant_",StringComparison.Ordinal)){response=PlantApi.Execute(operation,r);break;}
                    if(operation.StartsWith("material_",StringComparison.Ordinal)){response=MaterialApi.Execute(operation,r);break;}
                    throw new ApiException("unsupported_operation", "Use describe to discover operations.");
            }
            return JsonSerializer.Serialize(new { apiVersion=1, ok=true, result=response }, Json);
        }
        catch (Exception ex)
        {
            string code = ex is ApiException api ? api.Code : ex is NotSupportedException ? "unsupported_view" :
                ex is JsonException or ArgumentException or KeyNotFoundException or InvalidOperationException or FormatException ? "invalid_request" : "export_failed";
            return JsonSerializer.Serialize(new { apiVersion=1, ok=false, error=new { code, message=ex.Message } }, Json);
        }
    }

    private static RhinoDoc Document(JsonElement request)
    {
        uint serial = request.GetProperty("document").GetUInt32();
        var doc = RhinoDoc.FromRuntimeSerialNumber(serial) ?? throw new ApiException("document_not_found", "Document is closed or serial is invalid.");
        if (doc.IsHeadless) throw new ApiException("unsupported_view", "An interactive model viewport is required.");
        return doc;
    }

    private static void Merge(JsonObject target,JsonObject patch)
    {
        foreach(var pair in patch)
        {
            if(pair.Key is "id" or "name")continue;
            if(pair.Value is JsonObject child&&target[pair.Key] is JsonObject old)Merge(old,child);
            else target[pair.Key]=pair.Value?.DeepClone();
        }
    }

    private sealed class ApiException(string code, string message) : Exception(message) { public string Code { get; } = code; }
}

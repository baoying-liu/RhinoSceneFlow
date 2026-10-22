using RhinoSceneFlow.Core;
using System.Text.Json;
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
                case "describe":
                    response = new { name = "RhinoSceneFlow", version = "0.5.0", transport = "Rhino-MCP-Platform.run_python",
                        entryPoint = "RhinoSceneFlow.Plugin.McpApi.Execute(string)",
                        operations = new object[] {
                            new { name="open_panel", required=new[]{"document"}, parameters="Opens or activates the native Eto Named View export panel", output="Panel state" },
                            new { name="panel_status", required=new[]{"document"}, parameters="Read-only panel state", output="Panel state, or open=false" },
                            new { name="named_views", required=new[]{"document"}, parameters="Lists stable named-view IDs and default dimensions", output="Named View entries" },
                            new { name="export_named_views", required=new[]{"document","directory","views"}, parameters="views: [{viewId,width,height}]; channels?: [material,shadow] (material currently layer RGB); collision?: number (default), overwrite, cancel; writes one PSD per Named View", output="Batch files, dimensions, layer counts, timing and per-view errors" },
                            new { name="describe", required=Array.Empty<string>(), parameters="apiVersion=1", output="Version, operation contracts, limitations" },
                            new { name="status", required=new[]{"document"}, parameters="document: Rhino runtime serial number", output="Default directory, document and active viewport" },
                            new { name="configure_export", required=new[]{"directory"}, parameters="directory: absolute path; directory is created on export", output="Persisted default export directory" },
                            new { name="export_shadow_psd", required=new[]{"document"}, parameters="width?, path?, viewportId?, overwrite?; toSun?: [x,y,z] surface-to-sun direction (default enabled Rhino sun or [-1,-1,2]); color?: #RRGGBB (default #5A5A5A); opacity?: (0,1] default 1; includeFormShading?: false; bias?: positive model units; backend?: ray (legacy default) or volume (z-fail volumes with original-surface refinement)", output="Export report (including surfaceRefinements query count) plus normalized light direction, source, style, bias, backend and empty flag" },
                            new { name="export_psd", required=new[]{"document"}, parameters="width?: 64..8192 (default 2048), path?: absolute .psd (default generated), viewportId?: expected active viewport GUID, overwrite?: false", output="File path, dimensions, layers, object/triangle counts, skipped types, timing" }
                        }, limits = new { maxPixels=8_000_000, maxSide=8192, bitDepth=8, grouping="layer_rgb", appearance="opaque_flat_color" } };
                    break;
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
                        r.TryGetProperty("includeFormShading", out var form) && form.GetBoolean(),
                        r.TryGetProperty("bias", out var bias) ? bias.GetDouble() : null,
                        r.TryGetProperty("backend", out var backend) ? backend.GetString() ?? "ray" : "ray");
                    break;
                case "export_psd":
                    response = ExportService.Export(Document(r), r.TryGetProperty("width", out var width) ? width.GetInt32() : 2048,
                        r.TryGetProperty("path", out var path) ? path.GetString() : null,
                        r.TryGetProperty("overwrite", out var overwrite) && overwrite.GetBoolean(),
                        r.TryGetProperty("viewportId", out var viewport) ? Guid.Parse(viewport.GetString()!) : null);
                    break;
                default: throw new ApiException("unsupported_operation", "Use describe to discover operations.");
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

    private sealed class ApiException(string code, string message) : Exception(message) { public string Code { get; } = code; }
}

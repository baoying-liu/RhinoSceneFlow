using System.Text.Json;
using Rhino;
using Rhino.Geometry;
using RhinoSceneFlow.Core;
namespace RhinoSceneFlow.Plugin;
internal static class PlantApi
{
    private static Guid Id(JsonElement r,string key="assetId")=>Guid.Parse(r.GetProperty(key).GetString()!);
    private static T Read<T>(JsonElement r,string key)=>JsonSerializer.Deserialize<T>(r.GetProperty(key).GetRawText(),MaterialLibrary.Json)!;
    private static double Number(JsonElement r,string key,double fallback)=>r.TryGetProperty(key,out var v)?v.GetDouble():fallback;
    private static int Int(JsonElement r,string key,int fallback)=>(int)Number(r,key,fallback);
    private static bool Mirror(JsonElement r)=>!r.TryGetProperty("mirror",out var m)||m.GetBoolean();
    private static RhinoDoc Doc(JsonElement r){var d=RhinoDoc.FromRuntimeSerialNumber(r.GetProperty("document").GetUInt32())??throw new ArgumentException("文档不存在。");NamedViewExportService.RequireActive(d);return d;}
    internal static readonly string[] Operations=["plant_library","plant_import","plant_update","plant_select","plant_place","plant_scatter","plant_settings","plant_instances","plant_organize"];
    internal static object Execute(string op,JsonElement r)=>op switch
    {
        "plant_library"=>new{directory=PlantService.Library.Root,assets=PlantService.Library.List(r.TryGetProperty("query",out var q)?q.GetString()??"":"")},
        "plant_import"=>PlantService.Import(Read<MaterialAsset>(r,"asset"),r.GetProperty("path").GetString()!),
        "plant_update"=>PlantService.Library.Update(Read<MaterialAsset>(r,"asset")),
        "plant_select"=>Select(Doc(r),Id(r)),
        "plant_place"=>new{objects=PlantService.Place(Doc(r),Id(r),Read<double[][]>(r,"points").Select(p=>p.Length==3?new Point3d(p[0],p[1],p[2]):throw new ArgumentException("points: [[x,y,z]] document units")).ToArray(),Int(r,"seed",42),Number(r,"minScale",1),Number(r,"maxScale",1),Mirror(r))},
        "plant_scatter"=>PlantService.Scatter(Doc(r),Id(r),Id(r,"surfaceId"),Int(r,"count",20),Number(r,"spacingMeters",1),Int(r,"seed",42),Number(r,"minScale",.85),Number(r,"maxScale",1.15),Mirror(r)),
        "plant_settings"=>Settings(r),
        "plant_instances"=>new{objects=PlantService.Visible(Doc(r),Doc(r).Views.ActiveView.ActiveViewport).Select(o=>new{id=o.Id,settings=PlantService.Read(o),position=((Rhino.Geometry.Point)o.Geometry).Location}).ToArray()},
        "plant_organize"=>CatalogService.Organize(true),
        _=>throw new ArgumentException("未知植物操作。")
    };
    private static object Settings(JsonElement r){if(r.TryGetProperty("settings",out _))PlantService.Settings=Read<BillboardSettings>(r,"settings");return PlantService.Settings;}
    private static object Select(RhinoDoc doc,Guid id){PlantService.Library.Get(id);PlantService.Selected[doc.RuntimeSerialNumber]=id;SceneFlowWorkspace.Open("planting");SceneFlowWorkspace.Planting!.Select(id);return SceneFlowWorkspace.Planting.State();}
}

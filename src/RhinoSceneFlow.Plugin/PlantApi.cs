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
    internal static readonly string[] Operations=["plant_edit_transform","plant_edit_cancel","plant_edit_pick","plant_loose_update","plant_list_select","plant_group_manage","plant_edit_enter","plant_edit_exit","plant_edit_status","plant_individual_update","plant_ui_settings","plant_localize_names","plant_group_create","plant_group_update","plant_group_state","plant_group_list","plant_group_manual","plant_library","plant_import","plant_update","plant_select","plant_place","plant_scatter","plant_settings","plant_instances","plant_organize"];
    internal static object Execute(string op,JsonElement r)=>op switch
    {
        "plant_edit_transform"=>EditTransform(Doc(r),r),
        "plant_edit_cancel"=>CancelEdit(),
        "plant_edit_pick"=>Pick(Doc(r),r),
        "plant_loose_update"=>Loose(Doc(r),r),
        "plant_list_select"=>ListSelect(Doc(r),r),
        "plant_group_manage"=>PlantsListTool.Manage(Doc(r),Read<Guid[]>(r,"groups"),r.TryGetProperty("name",out var gn)?gn.GetString():null,r.TryGetProperty("layerId",out _)?Id(r,"layerId"):null,r.TryGetProperty("visible",out var gv)?gv.GetBoolean():null,r.TryGetProperty("locked",out var gl)?gl.GetBoolean():null),
        "plant_edit_enter"=>Edit(Doc(r),r),
        "plant_edit_exit"=>ExitEdit(),
        "plant_edit_status"=>PlantEditing.State(),
        "plant_individual_update"=>Individual(Doc(r),r),
        "plant_library"=>new{directory=PlantService.Library.Root,assets=PlantService.Library.List(r.TryGetProperty("query",out var q)?q.GetString()??"":"")},
        "plant_import"=>PlantService.Import(Read<MaterialAsset>(r,"asset"),r.GetProperty("path").GetString()!),
        "plant_update"=>PlantService.Library.Update(Read<MaterialAsset>(r,"asset")),
        "plant_select"=>Select(Doc(r),Id(r)),
        "plant_place"=>new{objects=PlantService.Place(Doc(r),Id(r),Read<double[][]>(r,"points").Select(p=>p.Length==3?new Point3d(p[0],p[1],p[2]):throw new ArgumentException("points: [[x,y,z]] document units")).ToArray(),Int(r,"seed",42),Number(r,"minScale",1),Number(r,"maxScale",1),Mirror(r))},
        "plant_scatter"=>PlantService.Scatter(Doc(r),Id(r),Id(r,"surfaceId"),Int(r,"count",20),Number(r,"spacingMeters",1),Int(r,"seed",42),Number(r,"minScale",.85),Number(r,"maxScale",1.15),Mirror(r)),
        "plant_settings"=>Settings(r),
        "plant_instances"=>new{objects=PlantService.Drawables(Doc(r),Doc(r).Views.ActiveView.ActiveViewport).Select(o=>new{id=o.Billboard.Id,owner=o.Object.Id,manual=o.Manual,position=o.Billboard.GroundAnchor,displayPosition=o.Billboard.Anchor,heightMeters=o.Billboard.TreeHeight*RhinoMath.UnitScale(Doc(r).ModelUnitSystem,UnitSystem.Meters),orientation=o.Billboard.IsPlan?"plan":"elevation",scaleWidth=o.Billboard.Width}).ToArray()},
        "plant_organize"=>CatalogService.Organize(true),
        "plant_ui_settings"=>Preferences(r),
        "plant_localize_names"=>new{job=CatalogService.LocalizePlants()},
        "plant_group_create"=>new{id=PlantGroups.Create(Doc(r),Read<PlantGroupSpec>(r,"spec"))},
        "plant_group_update"=>UpdateGroup(Doc(r),r),
        "plant_group_manual"=>Manual(Doc(r),r),
        "plant_group_state"=>PlantGroups.State(Doc(r),Id(r,"groupId")),
        "plant_group_list"=>new{groups=PlantGroups.Objects(Doc(r)).Select(o=>PlantGroups.State(Doc(r),o.Id)).ToArray()},
        _=>throw new ArgumentException("未知植物操作。")
    };
    private static object CancelEdit(){PlantEditing.Cancel();return PlantEditing.State();}
    private static object EditTransform(RhinoDoc doc,JsonElement r)
    {
        var values=Read<double[]>(r,"transform");if(values.Length!=16||values.Any(v=>!double.IsFinite(v)))throw new ArgumentException("transform: 16 finite row-major values");var t=Transform.Identity;for(int i=0;i<16;i++)t[i/4,i%4]=values[i];
        return new{individualId=PlantEditing.ApplyTransform(doc,t,r.TryGetProperty("copy",out var copy)&&copy.GetBoolean())};
    }
    private static object Pick(RhinoDoc doc,JsonElement r)
    {
        var vp=doc.Views.ActiveView.ActiveViewport;if(r.TryGetProperty("viewportId",out var id)&&Guid.Parse(id.GetString()!)!=vp.Id)throw new ArgumentException("活动视口已变化。");
        return new{hit=PlantEditing.Pick(doc,vp,r.GetProperty("x").GetInt32(),r.GetProperty("y").GetInt32())};
    }
    private static object Loose(RhinoDoc doc,JsonElement r){var id=Id(r,"objectId");PlantEditing.ModifyLoose(doc,id,r.TryGetProperty("assetId",out _)?Id(r):null,r.TryGetProperty("scale",out var s)?s.GetDouble():null,r.TryGetProperty("mirror",out var m)?m.GetBoolean():null);return new{id};}
    private static object ListSelect(RhinoDoc doc,JsonElement r){SceneFlowWorkspace.Open("plantsList");var tool=(PlantsListTool)SceneFlowWorkspace.Hosts["plantsList"].Tool!;tool.Select(Read<Guid[]>(r,"groups"));tool.Refresh();return tool.State();}
    private static object Edit(RhinoDoc doc,JsonElement r){PlantEditing.Enter(doc,Id(r,"groupId"),r.TryGetProperty("individualId",out var row)?row.GetString():null);return PlantEditing.State();}
    private static object ExitEdit(){PlantEditing.Exit();return PlantEditing.State();}
    private static object Individual(RhinoDoc doc,JsonElement r)
    {
        Point3d? point=null;if(r.TryGetProperty("point",out _)){var p=Read<double[]>(r,"point");if(p.Length!=3||p.Any(v=>!double.IsFinite(v)))throw new ArgumentException("point: [x,y,z]");point=new(p[0],p[1],p[2]);}
        return new{individualId=PlantEditing.Modify(doc,Id(r,"groupId"),r.GetProperty("individualId").GetString()!,!r.TryGetProperty("custom",out var c)||c.GetBoolean(),r.TryGetProperty("assetId",out _)?Id(r):null,r.TryGetProperty("scale",out var scale)?scale.GetDouble():null,r.TryGetProperty("mirror",out var mirror)?mirror.GetBoolean():null,point)};
    }
    private static object Settings(JsonElement r){if(r.TryGetProperty("settings",out _))PlantService.Settings=Read<BillboardSettings>(r,"settings");return PlantService.Settings;}
    private static object Preferences(JsonElement r)
    {
        var p=PlantUiPreferences.Load();if(r.TryGetProperty("settings",out var values))
        {if(values.TryGetProperty("language",out var l))p.Language=l.GetString()!;if(values.TryGetProperty("libraryView",out var v))p.LibraryView=v.GetString()!;if(values.TryGetProperty("compositionView",out var c))p.CompositionView=c.GetString()!;return PlantUiPreferences.Save(p);}return p;
    }
    private static object UpdateGroup(RhinoDoc doc,JsonElement r)
    {
        var id=Id(r,"groupId");var obj=doc.Objects.FindId(id)??throw new ArgumentException("种植对象不存在。");var spec=r.TryGetProperty("spec",out _)?Read<PlantGroupSpec>(r,"spec"):PlantGroups.Read(obj)??throw new ArgumentException("不是种植组合。");
        if(r.TryGetProperty("settings",out _))spec.Settings=Read<PlantLayoutSettings>(r,"settings");if(r.TryGetProperty("palette",out _))spec.Palette=Read<PlantPaletteItem[]>(r,"palette");if(r.TryGetProperty("surfaceId",out _))spec.Surface=Id(r,"surfaceId");PlantGroups.Update(doc,id,spec);return PlantGroups.State(doc,id);
    }
    private static object Manual(RhinoDoc doc,JsonElement r){var p=Read<double[]>(r,"point");if(p.Length!=3)throw new ArgumentException("point: [x,y,z]");var id=Id(r,"groupId");PlantGroups.AddManual(doc,id,Id(r),new Point3d(p[0],p[1],p[2]));return PlantGroups.State(doc,id);}
    private static object Select(RhinoDoc doc,Guid id){PlantService.Library.Get(id);PlantService.Selected[doc.RuntimeSerialNumber]=id;SceneFlowWorkspace.Open("planting");SceneFlowWorkspace.Planting!.Select(id);return SceneFlowWorkspace.Planting.State();}
}

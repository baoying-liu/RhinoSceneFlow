using Rhino;
using Rhino.DocObjects;
using Rhino.Geometry;
using Rhino.Input.Custom;
using Rhino.UI;
using RhinoSceneFlow.Core;

namespace RhinoSceneFlow.Plugin;

/// <summary>Selection is transient; persistent edits live on the group, never on temporary document objects.</summary>
public static partial class PlantEditing
{
    public sealed record Hit(Guid GroupId,string IndividualId,double Distance);
    public static Guid? Group {get;private set;}
    public static string? Individual {get;private set;}
    private static uint document;
    private static Picker? picker;
    internal static bool Selected(uint doc,Guid group,string row)=>document==doc&&Group==group&&Individual==row;
    internal static bool IsEditing(uint doc,Guid group)=>document==doc&&Group==group;
    internal static void Start(){picker=new(){Enabled=true};RhinoDoc.CloseDocument+=Closed;StartIsolationLifecycle();}
    internal static void Stop(){if(picker!=null)picker.Enabled=false;picker=null;RhinoDoc.CloseDocument-=Closed;Exit();StopIsolationLifecycle();}
    private static void Closed(object? s,DocumentEventArgs e){if(e.Document.RuntimeSerialNumber==document)Exit();}
    public static object State()=>new{document,group=Group,individual=Individual,isolated=isolated!=null,lockedOutside=isolated?.Modes.Count??0,gumball=handle?.Enabled==true,dragging,dragCopy};
    public static void Enter(RhinoDoc doc,Guid id,string? row=null)
    {
        if(IsActive(doc.RuntimeSerialNumber)&&Group!=id&&doc.Objects.FindId(id)?.Attributes.GetUserString(LockKey)!=null)Exit();
        NamedViewExportService.RequireActive(doc);var obj=doc.Objects.FindId(id)??throw new ArgumentException("组合不存在。");
        if(!PlantGroups.IsGroup(obj)||(!IsEditing(doc.RuntimeSerialNumber,id)&&(obj.IsHidden||obj.IsLocked||!obj.IsSelectable(true,false,false,false))))throw new ArgumentException("请先显示并解锁组合及所在图层。");
        PlantGroups.RequireReady(doc,obj);if(row!=null&&!PlantGroups.Rows(obj).Any(r=>r.Id==row))throw new ArgumentException("单株已变化，请重新选择。");
        if(!IsEditing(doc.RuntimeSerialNumber,id)){Exit();document=doc.RuntimeSerialNumber;Group=id;BeginIsolation(doc,obj);}
        Individual=row;doc.Objects.UnselectAll();SyncHandle();
        SceneFlowWorkspace.Open("properties");doc.Views.Redraw();
    }
    public static void Exit()=>EndIsolation(false);
    public static void Cancel()=>EndIsolation(true);
    public static string Modify(RhinoDoc doc,Guid group,string rowId,bool custom=true,Guid? asset=null,double? scale=null,bool? mirror=null,Point3d? position=null)
    {
        NamedViewExportService.RequireActive(doc);var obj=doc.Objects.FindId(group)??throw new ArgumentException("组合不存在。");
        if(!IsEditing(doc.RuntimeSerialNumber,group)&&(obj.IsLocked||obj.IsHidden||!obj.IsSelectable(true,false,false,false)))throw new ArgumentException("请先显示并解锁组合及所在图层。");
        PlantGroups.RequireReady(doc,obj);var spec=PlantGroups.Read(obj)??throw new ArgumentException("不是植物组合。");
        var individual=spec.Individuals.FirstOrDefault(i=>i.Id==rowId);var row=PlantGroups.Rows(obj).FirstOrDefault(r=>r.Id==rowId)??throw new ArgumentException("单株已变化。");
        PlantGroups.FreezeLayout(doc,obj,spec);
        if(!custom){spec.Individuals=spec.Individuals.Where(i=>i.Id!=rowId).ToArray();WriteIndividual(doc,group,spec);Individual=null;SyncHandle();return individual?.OriginalId??rowId;}
        if(!PlantGroups.Matrix(obj).TryGetInverse(out var inverse))throw new ArgumentException("组合变换不可逆。");
        double units=RhinoMath.UnitScale(doc.ModelUnitSystem,UnitSystem.Meters);
        var carrier=doc.Objects.FindId(spec.Surface)??throw new ArgumentException("承载面已删除，请重新关联。");
        if(individual==null)
        {
            string id="custom:"+Guid.NewGuid().ToString("N");var p=inverse*new Point3d(row.Position.X/units,row.Position.Y/units,row.Position.Z/units);
            var attachment=PlantGroups.Attach(carrier.Geometry,p,row.Asset);attachment.Id=id;
            var original=row with{Position=new(p.X*units,p.Y*units,p.Z*units)};
            individual=new(){Id=id,OriginalId=row.Id,OriginalSeed=spec.Settings.LayoutSeed,WasManual=row.Manual,Attachment=attachment,Scale=row.Scale,Mirror=row.Mirror,Original=original};spec.Individuals=[..spec.Individuals,individual];
        }
        if(asset.HasValue){var next=PlantService.Library.Get(asset.Value);if(next.Plant==null)throw new ArgumentException("请选择植物素材。");individual.Scale*=spec.Assets[individual.Attachment.Asset].HeightMeters/next.HeightMeters;individual.Attachment.Asset=asset.Value;}
        if(scale.HasValue)individual.Scale=scale.Value;if(mirror.HasValue)individual.Mirror=mirror.Value;
        if(position.HasValue){individual.Attachment=PlantGroups.Attach(carrier.Geometry,inverse*position.Value,individual.Attachment.Asset);individual.Attachment.Id=individual.Id;}
        WriteIndividual(doc,group,spec);if(document==doc.RuntimeSerialNumber&&Group==group)Individual=individual.Id;SyncHandle();return individual.Id;
    }
    internal static void Move(RhinoDoc doc)
    {
        if(Group is not Guid group||Individual is not string row)throw new ArgumentException("先在组合中选择一株植物。");
        var obj=doc.Objects.FindId(group)!;var spec=PlantGroups.Read(obj)!;var carrier=doc.Objects.FindId(spec.Surface)??throw new ArgumentException("承载面已删除。");
        using var mesh=PlantGroups.MeshFor(carrier.Geometry);mesh.Transform(PlantGroups.Matrix(obj));using var point=new GetPoint();
        point.SetCommandPrompt("移动单株植物 · 吸附承载面 · Esc 取消");point.Constrain(mesh,false);
        PlantGroups.Picking=true;try{if(point.Get()==Rhino.Input.GetResult.Point)Modify(doc,group,row,position:point.Point());}finally{PlantGroups.Picking=false;}
    }
    public static void ModifyLoose(RhinoDoc doc,Guid id,Guid? asset=null,double? scale=null,bool? mirror=null)
    {
        NamedViewExportService.RequireActive(doc);var obj=doc.Objects.FindId(id)??throw new ArgumentException("植物不存在。");var plant=PlantService.Read(obj)??throw new ArgumentException("不是独立植物。");
        if(!obj.IsSelectable(true,false,false,false))throw new ArgumentException("请先显示并解锁植物。");
        if(asset is Guid nextId){var next=PlantService.Library.Get(nextId);if(next.Plant==null)throw new ArgumentException("请选择植物素材。");PlantService.Library.Verify(next);plant.Scale*=plant.HeightMeters/next.HeightMeters;plant.Asset=next.Id;plant.WidthMeters=next.WidthMeters;plant.HeightMeters=next.HeightMeters;plant.Image=PlantService.Library.MapPath(next,"baseColor");plant.Sha256=next.Sha256["baseColor"];plant.ScientificName=next.Plant.ScientificName;plant.AnchorU=next.Plant.AnchorU;plant.AnchorV=next.Plant.AnchorV;}
        if(scale.HasValue)plant.Scale=scale.Value;if(mirror.HasValue)plant.Mirror=mirror.Value;if(!double.IsFinite(plant.Scale)||plant.Scale<=0||plant.Scale>100)throw new ArgumentException("植物比例需为 0–100。");
        var attrs=obj.Attributes.Duplicate();attrs.SetUserString(PlantService.Key,MaterialService.Serialize(plant));uint undo=doc.BeginUndoRecord("修改独立植物");try{if(!doc.Objects.ModifyAttributes(id,attrs,true))throw new InvalidOperationException("无法修改植物。");}finally{if(undo!=0)doc.EndUndoRecord(undo);}doc.Views.Redraw();
    }
    public static Hit? Pick(RhinoDoc doc,Rhino.Display.RhinoViewport vp,int x,int y)
    {
        NamedViewExportService.RequireActive(doc);if(!vp.GetFrustumLine(x,y,out var line))return null;
        // Rhino can return far -> near. Occlusion requires a ray pointing away from the camera.
        if(line.Direction*vp.CameraDirection<0)line.Flip();
        var origin=new Vec3(line.From.X,line.From.Y,line.From.Z);var direction=new Vec3(line.Direction.X,line.Direction.Y,line.Direction.Z).Unit;
        var camera=PlantService.Camera(vp);double nearest=double.PositiveInfinity;Hit? hit=null;
        var ray=new Ray3d(line.From,new Vector3d(direction.X,direction.Y,direction.Z));
        var blockers=doc.Objects.GetObjectList(new ObjectEnumeratorSettings{NormalObjects=true,LockedObjects=true,HiddenObjects=false,VisibleFilter=true,ViewportFilter=vp,IdefObjects=false}).Where(o=>!PlantService.IsPlant(o)).ToArray();
        foreach(var blocker in blockers)
        {
            var overrideId=blocker.Attributes.GetDisplayModeOverride(vp.Id);
            var mode=overrideId==Guid.Empty?vp.DisplayMode:Rhino.Display.DisplayModeDescription.GetDisplayMode(overrideId)??vp.DisplayMode;
            if(!mode.DisplayAttributes.ShadingEnabled||mode.DisplayAttributes.XrayAllObjects)continue;
            if(blocker.Geometry is Mesh mesh){double t=Rhino.Geometry.Intersect.Intersection.MeshRay(mesh,ray);if(t>0)nearest=Math.Min(nearest,t);}
            else if(blocker.Geometry is Brep or Surface or Extrusion)
            {var points=Rhino.Geometry.Intersect.Intersection.RayShoot(ray,[blocker.Geometry],1);if(points is {Length:>0})nearest=Math.Min(nearest,line.From.DistanceTo(points[0]));}
        }
        foreach(var entry in PlantService.NativeDrawables(doc,vp).Where(p=>PlantGroups.IsGroup(p.Object)&&(IsActive(doc.RuntimeSerialNumber)?IsEditing(doc.RuntimeSerialNumber,p.Object.Id):p.Object.IsSelectable(true,false,false,false))))
        {
            var b=entry.Billboard;var axes=b.Axes(camera,PlantService.Settings);var n=axes.Right.Cross(axes.Up);double den=direction.Dot(n);if(Math.Abs(den)<1e-10)continue;
            // Match the native preview's depth separation and visible-alpha threshold.
            var anchor=b.Anchor+camera.Back*(Math.Max(b.Width,b.Height)*1e-5);
            double t=(anchor-origin).Dot(n)/den;if(t<=0||t>=nearest)continue;var delta=origin+direction*t-anchor;
            double u=delta.Dot(axes.Right)/b.Width+b.PivotU,v=delta.Dot(axes.Up)/b.Height+b.AnchorV;
            if(u<0||u>1||v<0||v>1||b.Image.Sample(b.Mirror?1-u:u,v).A<.02)continue;
            nearest=t;hit=new(entry.Object.Id,b.Id[(b.Id.IndexOf('/')+1)..],t);
        }
        return hit;
    }
    private sealed class Picker:MouseCallback
    {
        protected override void OnMouseDown(MouseCallbackEventArgs e)=>Handle(e,false);
        // Rhino dispatches WM_LBUTTONDBLCLK separately; the second click is not a second OnMouseDown.
        protected override void OnMouseDoubleClick(MouseCallbackEventArgs e)=>Handle(e,true);
        private static void Handle(MouseCallbackEventArgs e,bool doubleClick)
        {
            if(e.Button!=System.Windows.Forms.MouseButtons.Left||RhinoApp.InCommand>0||PlantGroups.Picking)return;
            var doc=e.View.Document;if(doc==null||!doc.IsAvailable||doc.IsClosing||doc.IsOpening)return;
            if(!doubleClick&&(document!=doc.RuntimeSerialNumber||Group==null))return;
            try
            {
                if(IsActive(doc.RuntimeSerialNumber))
                {
                    e.Cancel=true;
                    if(!doubleClick&&TryHandleDrag(doc,e))return;
                }
                // A selected root's native Gumball must not veto an actual plant double-click.
                var hit=Pick(doc,e.View.ActiveViewport,e.ViewportPoint.X,e.ViewportPoint.Y);
                if(hit==null){if(doubleClick&&IsActive(doc.RuntimeSerialNumber)){Exit();e.Cancel=true;}return;}
                if(doubleClick){Enter(doc,hit.GroupId,hit.IndividualId);e.Cancel=true;}
                else if(IsEditing(doc.RuntimeSerialNumber,hit.GroupId))
                {Individual=hit.IndividualId;e.Cancel=true;SyncHandle();SceneFlowWorkspace.Open("properties");doc.Views.Redraw();}
            }
            catch(Exception ex){RhinoApp.WriteLine("SceneFlow: "+ex.Message);}
        }
    }
}

public sealed class PlantEditCommand:Rhino.Commands.Command
{
    public override string EnglishName=>"RhinoSceneFlowPlantEdit";
    protected override Rhino.Commands.Result RunCommand(RhinoDoc doc,Rhino.Commands.RunMode mode)
    {
        try{var groups=doc.Objects.GetSelectedObjects(false,false).Where(PlantGroups.IsGroup).ToArray();if(groups.Length!=1)throw new ArgumentException("先选择一个 Plants Group。");PlantEditing.Enter(doc,groups[0].Id);return Rhino.Commands.Result.Success;}
        catch(Exception e){RhinoApp.WriteLine(e.Message);return Rhino.Commands.Result.Failure;}
    }
}
public sealed class PlantEditEndCommand:Rhino.Commands.Command
{
    public override string EnglishName=>"RhinoSceneFlowPlantEditEnd";
    protected override Rhino.Commands.Result RunCommand(RhinoDoc doc,Rhino.Commands.RunMode mode){PlantEditing.Exit();return Rhino.Commands.Result.Success;}
}

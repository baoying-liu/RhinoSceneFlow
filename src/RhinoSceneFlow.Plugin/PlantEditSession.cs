using Eto.Forms;
using Rhino;
using Rhino.Commands;
using Rhino.DocObjects;
using Rhino.Geometry;
using Rhino.Input;
using Rhino.Input.Custom;
using Rhino.UI;
using Rhino.UI.Gumball;
using RhinoSceneFlow.Core;
using Command=Rhino.Commands.Command;

namespace RhinoSceneFlow.Plugin;

public static partial class PlantEditing
{
    private const string LockKey="RhinoSceneFlow.PlantEdit.Lock.v1";
    private sealed class Isolation
    {
        internal readonly Dictionary<Guid,ObjectMode> Modes=[];
        internal string Spec="",Name="";internal Guid[] Selection=[];
    }
    private static Isolation? isolated;
    private static GumballDisplayConduit? handle;
    private static UITimer? handles;
    private static string handleStamp="";
    private static bool changing,dragging;
    private static bool dragCopy;
    private static string? dragRow;
    private static Transform preview=Transform.Identity;
    internal static bool Applying {get;private set;}
    internal static bool IsActive(uint serial)=>document==serial&&Group!=null&&isolated!=null;
    internal static void RequireFinished(RhinoDoc doc){if(IsActive(doc.RuntimeSerialNumber))throw new InvalidOperationException("请先完成或取消单株编辑，再导出。");}
    private static void StartIsolationLifecycle()
    {
        handles=new(){Interval=.15};handles.Elapsed+=(_,_)=>{try{SyncHandle();}catch(Exception e){System.Diagnostics.Debug.WriteLine(e.Message);}};handles.Start();
        RhinoDoc.BeginSaveDocument+=Saving;RhinoDoc.EndOpenDocument+=Opened;Command.UndoRedo+=UndoEnded;
    }
    private static void StopIsolationLifecycle(){handles?.Stop();handles?.Dispose();handles=null;RhinoDoc.BeginSaveDocument-=Saving;RhinoDoc.EndOpenDocument-=Opened;Command.UndoRedo-=UndoEnded;}
    private static void Saving(object? sender,DocumentSaveEventArgs e){if(IsActive(e.Document.RuntimeSerialNumber)){Exit();RhinoApp.WriteLine("已完成植物单株编辑，继续保存。");}}
    private static void Opened(object? sender,DocumentOpenEventArgs e)=>RepairLocks(e.Document);
    private static void UndoEnded(object? sender,UndoRedoEventArgs e)
    {
        if(!e.IsEndUndo&&!e.IsEndRedo)return;var doc=RhinoDoc.ActiveDoc;if(doc==null||!doc.IsAvailable||doc.IsClosing)return;
        if(IsActive(doc.RuntimeSerialNumber))LockScene(doc);else RepairLocks(doc);handleStamp="";
    }
    private static void BeginIsolation(RhinoDoc doc,RhinoObject root)
    {
        isolated=new(){Spec=root.Attributes.GetUserString(PlantGroups.Key)!,Name=root.Name,Selection=doc.Objects.GetSelectedObjects(false,false).Select(o=>o.Id).ToArray()};
        try{LockScene(doc);doc.Objects.UnselectAll();handle=new(ActiveSpace.ModelSpace);handleStamp="";RhinoApp.WriteLine("植物单株编辑：只操作当前组合；点击一株后拖动其操作柄，Ctrl 拖动复制单株。完成或取消请使用属性工具。");}
        catch{EndIsolation(false);throw;}
    }
    private static void LockScene(RhinoDoc doc)
    {
        if(isolated==null||changing)return;bool undo=doc.UndoRecordingEnabled,modified=doc.Modified;changing=true;
        try
        {
            doc.UndoRecordingEnabled=false;
            foreach(var obj in doc.Objects.GetObjectList(new ObjectEnumeratorSettings{NormalObjects=true,LockedObjects=true,HiddenObjects=true}))
            {
                if(obj.IsReference||obj.IsInstanceDefinitionGeometry)continue;
                if(obj.Attributes.Mode!=ObjectMode.Normal&&!isolated.Modes.ContainsKey(obj.Id))continue;
                if(!isolated.Modes.ContainsKey(obj.Id))isolated.Modes[obj.Id]=obj.Attributes.Mode;
                if(obj.IsLocked&&obj.Attributes.GetUserString(LockKey)!=null)continue;
                var a=obj.Attributes.Duplicate();a.SetUserString(LockKey,((int)isolated.Modes[obj.Id]).ToString(System.Globalization.CultureInfo.InvariantCulture));a.Mode=ObjectMode.Locked;
                if(!doc.Objects.ModifyAttributes(obj.Id,a,true))throw new InvalidOperationException("无法隔离外部物件。");
            }
        }
        finally{doc.UndoRecordingEnabled=undo;doc.Modified=modified;changing=false;}
    }
    private static void RepairLocks(RhinoDoc doc)
    {
        if(!doc.IsAvailable||doc.IsClosing||IsActive(doc.RuntimeSerialNumber)||changing)return;bool undo=doc.UndoRecordingEnabled,modified=doc.Modified;changing=true;
        try{doc.UndoRecordingEnabled=false;foreach(var obj in doc.Objects.GetObjectList(new ObjectEnumeratorSettings{NormalObjects=true,LockedObjects=true,HiddenObjects=true}))
        {string? old=obj.Attributes.GetUserString(LockKey);if(old==null)continue;if(!int.TryParse(old,out int value)||!Enum.IsDefined(typeof(ObjectMode),value))continue;var a=obj.Attributes.Duplicate();a.Mode=(ObjectMode)value;a.SetUserString(LockKey,null);doc.Objects.ModifyAttributes(obj.Id,a,true);}}
        finally{doc.UndoRecordingEnabled=undo;doc.Modified=modified;changing=false;}
    }
    private static void EndIsolation(bool cancel)
    {
        var doc=RhinoDoc.FromRuntimeSerialNumber(document);var saved=isolated;var id=Group;EndPreview();handle?.Dispose();handle=null;handleStamp="";preview=Transform.Identity;
        try
        {
            if(doc?.IsAvailable==true&&!doc.IsClosing&&cancel&&saved!=null&&id is Guid root&&doc.Objects.FindId(root) is {} obj&&obj.Attributes.GetUserString(PlantGroups.Key)!=saved.Spec)
            {
                uint undo=doc.BeginUndoRecord("取消植物单株编辑");try{var a=obj.Attributes.Duplicate();a.SetUserString(PlantGroups.Key,saved.Spec);a.Name=saved.Name;PlantParameterUndo.Record(doc,obj,saved.Spec,saved.Name);if(!doc.Objects.ModifyAttributes(root,a,true))throw new InvalidOperationException("无法恢复编辑前的植物组合。");}finally{if(undo!=0)doc.EndUndoRecord(undo);}
            }
        }
        finally
        {
            isolated=null;Group=null;Individual=null;document=0;
            if(doc?.IsAvailable==true&&!doc.IsClosing){RepairLocks(doc);foreach(var selected in saved?.Selection??[])if(doc.Objects.FindId(selected)?.IsSelectable(true,false,false,false)==true)doc.Objects.Select(selected);doc.Views.Redraw();}
        }
    }
    private static void WriteIndividual(RhinoDoc doc,Guid id,PlantGroupSpec spec)
    {Applying=true;try{PlantGroups.Update(doc,id,spec);PlantGroups.CommitEdited(doc,id);}finally{Applying=false;}}
    private static double UniformScale(Transform transform)
    {
        var x=new Vector3d(1,0,0);var y=new Vector3d(0,1,0);var z=new Vector3d(0,0,1);x.Transform(transform);y.Transform(transform);z.Transform(transform);
        var values=new[]{x.Length,y.Length,z.Length};return values.OrderByDescending(v=>Math.Abs(v-1)).First();
    }
    internal static PlantBillboard Preview(PlantBillboard b,Guid owner)
    {
        if(!dragging||Group!=owner||dragRow==null||!b.Id.EndsWith("/"+dragRow,StringComparison.Ordinal))return b;
        var p=preview*new Point3d(b.Anchor.X,b.Anchor.Y,b.Anchor.Z);double scale=UniformScale(preview);
        return b with{Anchor=new(p.X,p.Y,p.Z),Width=b.Width*scale,Height=b.Height*scale,Mirror=b.Mirror^(preview.Determinant<0)};
    }
    internal static bool Moving(uint serial,Guid group,string row)=>document==serial&&Group==group&&dragging&&!dragCopy&&dragRow==row;
    internal static void BeginPreview(RhinoDoc doc,Rhino.Display.RhinoViewport viewport,bool copy)
    {
        if(!IsActive(doc.RuntimeSerialNumber)||Group is not Guid group||Individual is not string row)throw new InvalidOperationException("先选择要移动的单株。");
        var entry=PlantGroups.Drawables(doc,doc.Objects.FindId(group)!).First(e=>e.Billboard.Id.EndsWith("/"+row,StringComparison.Ordinal));
        PlantService.PrepareDrag(doc,viewport,entry);dragRow=row;dragCopy=copy;preview=Transform.Identity;dragging=true;
    }
    internal static void UpdatePreview(Transform transform){if(dragging)preview=transform;}
    internal static void EndPreview(){dragging=false;dragRow=null;dragCopy=false;preview=Transform.Identity;PlantService.EndDrag();}
    public static string ApplyTransform(RhinoDoc doc,Transform transform,bool copy=false)
    {
        if(!IsActive(doc.RuntimeSerialNumber)||Group is not Guid group||Individual is not string id)throw new InvalidOperationException("先进入单株编辑并选择一株植物。");
        if(!transform.IsValid||!transform.IsAffine)throw new ArgumentException("需要有效的仿射变换。");
        var obj=doc.Objects.FindId(group)??throw new ArgumentException("组合已删除。");PlantGroups.RequireReady(doc,obj);var row=PlantGroups.Rows(obj).First(r=>r.Id==id);
        double unit=RhinoMath.UnitScale(doc.ModelUnitSystem,UnitSystem.Meters);var point=transform*new Point3d(row.Position.X/unit,row.Position.Y/unit,row.Position.Z/unit);
        double scale=row.Scale*UniformScale(transform);bool mirror=row.Mirror^(transform.Determinant<0);
        if(!double.IsFinite(scale)||scale<=0||scale>100)throw new ArgumentException("植物比例需为 0–100。");
        if(!copy)return Modify(doc,group,id,scale:scale,mirror:mirror,position:point);
        // Copy adds an owned manual member, never a Rhino object or a second group.
        var spec=PlantGroups.Read(obj)!;PlantGroups.FreezeLayout(doc,obj,spec);var carrier=doc.Objects.FindId(spec.Surface)??throw new ArgumentException("承载面已删除。");
        PlantGroups.Matrix(obj).TryGetInverse(out var inverse);var attachment=PlantGroups.Attach(carrier.Geometry,inverse*point,row.Asset);
        string manualId=attachment.Id,customId="custom:"+Guid.NewGuid().ToString("N");
        var baseAsset=spec.Palette.Any(p=>p.Asset==row.Asset)?row.Asset:spec.Palette[0].Asset;
        var baseAttachment=PlantGroups.Attach(carrier.Geometry,inverse*point,baseAsset);baseAttachment.Id=manualId;spec.Manual=[..spec.Manual,baseAttachment];
        var local=new Vec3(baseAttachment.Position[0]*unit,baseAttachment.Position[1]*unit,baseAttachment.Position[2]*unit);
        var original=new LayoutPlant(manualId,baseAsset,local,true,row.Scale,row.Mirror);
        spec.EditLayout!.Rows=[..spec.EditLayout.Rows,original];spec.EditLayout.Key=PlantGroups.LayoutKey(doc,obj,spec);
        attachment.Id=customId;spec.Individuals=[..spec.Individuals,new(){Id=customId,OriginalId=manualId,WasManual=true,OriginalSeed=spec.Settings.LayoutSeed,Attachment=attachment,Scale=scale,Mirror=mirror,Original=original}];
        WriteIndividual(doc,group,spec);Individual=customId;SyncHandle();return customId;
    }
    private static void SyncHandle()
    {
        if(dragging||handle==null)return;var doc=RhinoDoc.FromRuntimeSerialNumber(document);
        if(doc==null||RhinoDoc.ActiveDoc?.RuntimeSerialNumber!=document||doc.IsClosing||Group is not Guid group||Individual is not string row||doc.Objects.FindId(group) is not {} root||PlantGroups.IsBusy(doc,group))
        {handle.Enabled=false;handleStamp="";return;}
        var billboard=PlantGroups.Drawables(doc,root).FirstOrDefault(e=>e.Billboard.Id.EndsWith("/"+row,StringComparison.Ordinal)).Billboard;
        if(billboard==null){handle.Enabled=false;handleStamp="";return;}
        string stamp=FormattableString.Invariant($"{billboard.Id}|{billboard.Anchor.X:R}|{billboard.Anchor.Y:R}|{billboard.Anchor.Z:R}|{billboard.Width:R}|{billboard.Height:R}|{billboard.Mirror}");if(stamp==handleStamp)return;
        using var source=new GumballObject();source.SetFromPlane(new(new Point3d(billboard.Anchor.X,billboard.Anchor.Y,billboard.Anchor.Z),Vector3d.ZAxis));
        var frame=source.Frame;frame.ScaleMode=GumballScaleMode.XYZ;source.Frame=frame;
        var appearance=new GumballAppearanceSettings{RelocateEnabled=false,MenuEnabled=false,RotateXEnabled=false,RotateYEnabled=false,RotateZEnabled=false,ScaleXEnabled=true,ScaleYEnabled=true,ScaleZEnabled=true};
        handle.PreTransform=Transform.Identity;handle.SetBaseGumball(source,appearance);handle.PickResult.SetToDefault();handle.Enabled=true;handleStamp=stamp;doc.Views.Redraw();
    }
    private static bool TryHandleDrag(RhinoDoc doc,MouseCallbackEventArgs e)
    {
        SyncHandle();if(handle?.Enabled!=true)return false;
        using var drag=new HandleDrag(handle){FullFrameRedrawDuringGet=false};drag.SetBasePoint(handle.BaseGumball.Frame.Plane.Origin,false);
        using var pick=new PickContext{View=e.View,PickStyle=PickStyle.PointPick};pick.SetPickTransform(e.View.ActiveViewport.GetPickTransform(e.ViewportPoint));
        e.View.ActiveViewport.GetFrustumLine(e.ViewportPoint.X,e.ViewportPoint.Y,out var line);pick.PickLine=line;pick.UpdateClippingPlanes();handle.PickResult.SetToDefault();
        if(!handle.PickGumball(pick,drag))return false;
        bool copy=e.CtrlKeyDown;BeginPreview(doc,e.View.ActiveViewport,copy);PlantGroups.Picking=true;
        try{doc.Views.Redraw();if(drag.Get(true)==GetResult.Point)ApplyTransform(doc,handle.TotalTransform,copy);}
        finally{EndPreview();PlantGroups.Picking=false;handleStamp="";SyncHandle();if(doc.IsAvailable&&!doc.IsClosing)doc.Views.Redraw();}
        return true;
    }
    private sealed class HandleDrag(GumballDisplayConduit display):GetTransform
    {
        public override Transform CalculateTransform(Rhino.Display.RhinoViewport viewport,Point3d point)=>dragging?display.TotalTransform:Transform.Identity;
        protected override void OnMouseMove(GetPointMouseEventArgs e)
        {
            if(!dragging)return;
            display.CheckShiftAndControlKeys();e.Viewport.GetFrustumLine(e.WindowPoint.X,e.WindowPoint.Y,out var ray);
            if(display.UpdateGumball(e.Point,ray)){UpdatePreview(display.TotalTransform);base.OnMouseMove(e);}
        }
        protected override void OnDynamicDraw(GetPointDrawEventArgs e)=>PlantService.DrawDrag(e.Display,e.Viewport);
    }
}

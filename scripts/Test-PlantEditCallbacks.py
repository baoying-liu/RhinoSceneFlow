"""Invoke the registered Rhino SDK mouse overrides after Platform completes; never inject OS input."""
import Rhino,System,clr,json,os,traceback
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi,PlantEditing,PlantGroups,PlantService
from System.Reflection import BindingFlags
from Eto.Forms import UITimer
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;flags=BindingFlags.Static|BindingFlags.Instance|BindingFlags.Public|BindingFlags.NonPublic
folder=os.path.join(OUTPUT_DIR,'plant-edit0171');root=System.Guid('73fb8208-d869-4935-bb7e-23a6e81e4641')
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
def queue():
 timer=UITimer();timer.Interval=.3;started=System.DateTime.UtcNow
 def tick(sender,args):
  try:
   if Rhino.RhinoApp.InCommand>0:
    assert (System.DateTime.UtcNow-started).TotalSeconds<15
    return
   timer.Stop();api('plant_edit_exit');vp=doc.Views.ActiveView.ActiveViewport
   pg=clr.GetClrType(PlantGroups);ps=clr.GetClrType(PlantService);pe=clr.GetClrType(PlantEditing)
   camera=ps.GetMethod('Camera',flags).Invoke(None,System.Array[System.Object]([vp]));settings=ps.GetProperty('Settings',flags).GetValue(None)
   hit=None;pixel=None
   for entry in pg.GetMethod('Drawables',flags).Invoke(None,System.Array[System.Object]([doc,doc.Objects.FindId(root)])):
    b=entry.Item2;axes=b.Axes(camera,settings);right=axes.Item1;up=axes.Item2
    for u in [.5,.3,.7]:
     for v in [.5,.3,.7,.85]:
      if b.Image.Sample(u,v).Item4<.6:continue
      du=(1-u if b.Mirror else u)-b.PivotU;dv=v-b.AnchorV
      p=Rhino.Geometry.Point3d(b.Anchor.X+right.X*du*b.Width+up.X*dv*b.Height,b.Anchor.Y+right.Y*du*b.Width+up.Y*dv*b.Height,b.Anchor.Z+right.Z*du*b.Width+up.Z*dv*b.Height)
      xy=vp.WorldToClient(p);x=int(xy.X);y=int(xy.Y)
      if x<0 or y<0 or x>=vp.Size.Width or y>=vp.Size.Height:continue
      candidate=PlantEditing.Pick(doc,vp,x,y)
      if candidate is not None and candidate.GroupId==root:hit=candidate;pixel=[x,y];break
     if hit is not None:break
    if hit is not None:break
   assert hit is not None,'No visible alpha pixel found'
   picker=pe.GetField('picker',flags).GetValue(None);ctor=clr.GetClrType(Rhino.UI.MouseCallbackEventArgs).GetConstructors(flags)[0]
   event=ctor.Invoke(System.Array[System.Object]([System.UInt32(doc.Views.ActiveView.RuntimeSerialNumber),System.UInt32(1),System.Int32(pixel[0]),System.Int32(pixel[1])]))
   method=picker.GetType().GetMethod('OnMouseDoubleClick',flags);method.Invoke(picker,System.Array[System.Object]([event]));state=api('plant_edit_status')
   assert event.Cancel and state['isolated'] and state['individual']==hit.IndividualId and state['gumball'],state
   api('plant_edit_cancel')
   json.dump(dict(pid=EXPECTED_PID,pixel=pixel,nativeDoubleClick=True,callback=str(method.DeclaringType),selected=hit.IndividualId,noOSInput=True),open(os.path.join(folder,'callbacks.json'),'w'),indent=2)
  except Exception:
   timer.Stop();json.dump(dict(error=traceback.format_exc(),pid=EXPECTED_PID),open(os.path.join(folder,'callbacks.json'),'w'),indent=2)
 timer.Elapsed+=tick;System.AppDomain.CurrentDomain.SetData('SceneFlowPlantCallbackTest',timer);timer.Start()
queue();print('SDK callback test queued')

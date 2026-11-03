"""Check the real conduit exposes pickable handles without an interactive Get/OS mouse input."""
import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi,PlantEditing,PlantGroups
from System.Reflection import BindingFlags
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;flags=BindingFlags.Static|BindingFlags.Public|BindingFlags.NonPublic;root=System.Guid('73fb8208-d869-4935-bb7e-23a6e81e4641')
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
row=list(clr.GetClrType(PlantGroups).GetMethod('Rows',flags).Invoke(None,System.Array[System.Object]([doc.Objects.FindId(root)])))[0]
api('plant_edit_enter',groupId=str(root),individualId=row.Id);handle=clr.GetClrType(PlantEditing).GetField('handle',flags).GetValue(None)
view=doc.Views.ActiveView;vp=view.ActiveViewport;origin=vp.WorldToClient(handle.BaseGumball.Frame.Plane.Origin)
from Rhino.Input.Custom import GetPoint
from Rhino.Input import GetResult
from Rhino.Display import RhinoViewport
gp=GetPoint();found={}
try:
 gp.SetBasePoint(handle.BaseGumball.Frame.Plane.Origin,False)
 for dx in range(-84,85,6):
  for dy in range(-84,85,6):
   x=int(origin.X)+dx;y=int(origin.Y)+dy
   if x<0 or y<0 or x>=vp.Size.Width or y>=vp.Size.Height:continue
   pick=Rhino.Input.Custom.PickContext()
   try:
    pick.View=view;pick.PickStyle=Rhino.Input.Custom.PickStyle.PointPick
    p=System.Drawing.Point(x,y);pick.SetPickTransform(vp.GetPickTransform(p));ok,line=vp.GetFrustumLine(x,y)
    pick.PickLine=line;pick.UpdateClippingPlanes();handle.PickResult.SetToDefault()
    if handle.PickGumball(pick,gp):found[str(handle.PickResult.Mode)]=[x,y]
   finally:pick.Dispose()
 assert any(k.startswith('Translate') for k in found),found
 assert any(k.startswith('Scale') for k in found),found
 json.dump(dict(pid=EXPECTED_PID,handles=found,uniformMode=str(handle.BaseGumball.Frame.ScaleMode),noOSInput=True),open(os.path.join(OUTPUT_DIR,'plant-edit0171','gumball.json'),'w'),indent=2)
 print(json.dumps(found))
finally:
 gp.Dispose();api('plant_edit_cancel')

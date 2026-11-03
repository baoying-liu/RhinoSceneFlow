"""Selection outline must change UI pixels only, never the ground shadow image."""
import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi,PlantEditing,PlantGroups,PlantService
from System.Reflection import BindingFlags
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'plant-outline0174');receipt=json.load(open(os.path.join(folder,'backup.json')));assert doc.Path==receipt['backup']
f=BindingFlags.Static|BindingFlags.Instance|BindingFlags.Public|BindingFlags.NonPublic;pg=clr.GetClrType(PlantGroups);ps=clr.GetClrType(PlantService);root=System.Guid('73fb8208-d869-4935-bb7e-23a6e81e4641');key=pg.GetField('Key',f).GetRawConstantValue();original=doc.Objects.FindId(root).Attributes.GetUserString(key)
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
rows=list(pg.GetMethod('Rows',f).Invoke(None,System.Array[System.Object]([doc.Objects.FindId(root)])));api('plant_edit_enter',groupId=str(root),individualId=rows[0].Id)
v=doc.Views.ActiveView;vp=v.ActiveViewport;camera=ps.GetMethod('Camera',f).Invoke(None,System.Array[System.Object]([vp]));settings=ps.GetProperty('Settings',f).GetValue(None);boxes=[]
for entry in pg.GetMethod('Drawables',f).Invoke(None,System.Array[System.Object]([doc,doc.Objects.FindId(root)])):
 b=entry.Item2;axes=b.Axes(camera,settings);right=axes.Item1;up=axes.Item2;points=[]
 for u,w in [(0,0),(1,0),(1,1),(0,1)]:
  du=u-b.PivotU;dv=w-b.AnchorV;p=Rhino.Geometry.Point3d(b.Anchor.X+right.X*du*b.Width+up.X*dv*b.Height,b.Anchor.Y+right.Y*du*b.Width+up.Y*dv*b.Height,b.Anchor.Z+right.Z*du*b.Width+up.Z*dv*b.Height);xy=vp.WorldToClient(p);points.append([xy.X,xy.Y])
 boxes.append([min(p[0] for p in points)-5,min(p[1] for p in points)-5,max(p[0] for p in points)+6,max(p[1] for p in points)+6])
def capture(name,shadows=True):
 mode=Rhino.Display.DisplayModeDescription.GetDisplayMode(vp.DisplayMode.Id);a=mode.DisplayAttributes;a.ShadowsOn=shadows
 b=v.CaptureToBitmap(vp.Size,a);b.Save(os.path.join(folder,name+'.png'),System.Drawing.Imaging.ImageFormat.Png);b.Dispose();mode.Dispose()
capture('fixed-outlined')
c=ps.GetField('conduit',f).GetValue(None);cache=c.GetType().GetField('previews',f).GetValue(c);saved=[]
for pair in cache:
 a=pair.Value.GetType().GetField('Outline',f).GetValue(pair.Value);saved.append((a,a.Clone()));System.Array.Clear(a,0,a.Length)
try:capture('fixed-no-outline');capture('fixed-no-shadows',False)
finally:
 for a,copy in saved:System.Array.Copy(copy,a,a.Length)
assert doc.Objects.FindId(root).Attributes.GetUserString(key)==original
json.dump(dict(pid=EXPECTED_PID,viewportSize=[vp.Size.Width,vp.Size.Height],plantBoxes=boxes,parametersUnchanged=True,shadowEnabled=vp.DisplayMode.DisplayAttributes.ShadowsOn),open(os.path.join(folder,'outline.json'),'w'),indent=2)
api('plant_edit_exit');print('Outline/shadow frames captured; original line arrays restored')

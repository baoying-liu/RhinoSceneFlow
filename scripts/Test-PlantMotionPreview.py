"""Native frames use the same renderer as GetPoint.OnDynamicDraw, without OS pointer input."""
import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi,PlantGroups,PlantEditing,PlantService
from System.Reflection import BindingFlags
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'plant-edit0173');record=json.load(open(os.path.join(folder,'backup.json')));assert doc.Path==record['backup']
f=BindingFlags.Static|BindingFlags.Public|BindingFlags.NonPublic;pg=clr.GetClrType(PlantGroups);pe=clr.GetClrType(PlantEditing);ps=clr.GetClrType(PlantService);root=System.Guid('73fb8208-d869-4935-bb7e-23a6e81e4641');key=pg.GetField('Key',f).GetRawConstantValue()
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
vp=doc.Views.ActiveView.ActiveViewport;view=doc.Views.ActiveView;camera=ps.GetMethod('Camera',f).Invoke(None,System.Array[System.Object]([vp]));settings=ps.GetProperty('Settings',f).GetValue(None)
source=None
for entry in pg.GetMethod('Drawables',f).Invoke(None,System.Array[System.Object]([doc,doc.Objects.FindId(root)])):
 b=entry.Item2;axes=b.Axes(camera,settings);r=axes.Item1;u=axes.Item2
 point=Rhino.Geometry.Point3d(b.Anchor.X+u.X*b.Height*.5,b.Anchor.Y+u.Y*b.Height*.5,b.Anchor.Z+u.Z*b.Height*.5);xy=vp.WorldToClient(point)
 if xy.X<80 or xy.X>vp.Size.Width-80 or xy.Y<80 or xy.Y>vp.Size.Height-80:continue
 hit=PlantEditing.Pick(doc,vp,int(xy.X),int(xy.Y))
 if hit is not None and hit.IndividualId==b.Id.split('/',1)[1]:source=b;break
assert source is not None,'No visible source tree'
row=source.Id.split('/',1)[1];api('plant_edit_enter',groupId=str(root),individualId=row);original=doc.Objects.FindId(root).Attributes.GetUserString(key)
def capture(name):
 b=view.CaptureToBitmap(vp.Size,vp.DisplayMode.DisplayAttributes);assert b is not None;b.Save(os.path.join(folder,name+'.png'),System.Drawing.Imaging.ImageFormat.Png);b.Dispose()
def invoke(name,*args):return pe.GetMethod(name,f).Invoke(None,System.Array[System.Object](list(args)))
drawTimes=[]
def overlay(sender,e):
 sw=System.Diagnostics.Stopwatch.StartNew();ps.GetMethod('DrawDrag',f).Invoke(None,System.Array[System.Object]([e.Display,e.Viewport]));drawTimes.append(sw.Elapsed.TotalMilliseconds)
attached=False
try:
 capture('motion-before');invoke('BeginPreview',doc,vp,False);assert api('plant_edit_status')['dragging']
 capture('motion-background');direction=camera.Right;sign=1 if xy.X<vp.Size.Width/2 else -1;distance=source.Width*1.5*sign
 transform=Rhino.Geometry.Transform.Translation(direction.X*distance,direction.Y*distance,direction.Z*distance);invoke('UpdatePreview',transform)
 Rhino.Display.DisplayPipeline.DrawForeground+=overlay;attached=True;capture('motion-a')
 invoke('UpdatePreview',Rhino.Geometry.Transform.Translation(-direction.X*distance,-direction.Y*distance,-direction.Z*distance));capture('motion-b')
 Rhino.Display.DisplayPipeline.DrawForeground-=overlay;attached=False;invoke('EndPreview');capture('motion-after')
 invoke('BeginPreview',doc,vp,True);capture('copy-background');invoke('EndPreview')
 axes=source.Axes(camera,settings);right=axes.Item1;up=axes.Item2;corners=[]
 for u,v in [(0,0),(1,0),(1,1),(0,1)]:
  du=u-source.PivotU;dv=v-source.AnchorV;p=Rhino.Geometry.Point3d(source.Anchor.X+right.X*du*source.Width+up.X*dv*source.Height,source.Anchor.Y+right.Y*du*source.Width+up.Y*dv*source.Height,source.Anchor.Z+right.Z*du*source.Width+up.Z*dv*source.Height);pt=vp.WorldToClient(p);corners.append([pt.X,pt.Y])
 assert doc.Objects.FindId(root).Attributes.GetUserString(key)==original
 json.dump(dict(pid=EXPECTED_PID,row=row,sourceCorners=corners,drawSubmissionMs=drawTimes,parametersUnchanged=True,noFullFrameDrag=True),open(os.path.join(folder,'preview.json'),'w'),indent=2)
 print('Dynamic preview frames captured')
finally:
 if attached:Rhino.Display.DisplayPipeline.DrawForeground-=overlay
 invoke('EndPreview');api('plant_edit_exit');doc.Views.Redraw()

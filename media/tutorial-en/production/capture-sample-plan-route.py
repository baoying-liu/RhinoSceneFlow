import Rhino,System,clr,json,os,math
from System.Reflection import BindingFlags
from System.Drawing.Imaging import ImageFormat
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import WorkbenchService,PlantService,McpApi
D=__rhino_doc__;assert 'material-check-owned.3dm' in D.Path
R=os.path.abspath(os.path.join(OUTPUT_DIR,'..','..'));out=os.path.join(R,'media','tutorial-en','public','case','promo-sample-v05','orbit','camera-route-fixed');os.makedirs(out,exist_ok=True)
# Restore cedar in this owned test case before recording the route.
layer=next(l for l in D.Layers if 'Cedar' in l.Name)
r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation='material_apply',document=int(D.RuntimeSerialNumber),assetId='da8e6581-808e-48ca-8e77-f63885689032',layers=[str(layer.Id)]))));assert r['ok'],r
view=D.Views.ActiveView;vp=view.ActiveViewport;saved=Rhino.DocObjects.ViewportInfo(vp);modified=D.Modified
row=next(r for r in WorkbenchService.Settings(D) if r.Name=='Promo Human').Copy();row.Width=1920;row.Height=1080
mode=next(m for m in Rhino.Display.DisplayModeDescription.GetDisplayModes() if m.EnglishName=='Rendered');row.Mode=mode.Id
named=next(n for n in D.NamedViews if n.Name=='Promo Human');info=named.Viewport;axis=info.CameraDirection;axis.Unitize();distance=(info.TargetPoint-info.CameraLocation)*axis
flags=BindingFlags.Static|BindingFlags.Public|BindingFlags.NonPublic;typ=clr.GetClrType(PlantService);method=typ.GetMethod('NativeDrawables',flags);proof=[]
try:
 settings=PlantService.Settings;assert settings.Mode=='auto' and abs(settings.PlanHeightRatio-.2)<1e-9
 for i in range(300):
  path=os.path.join(out,'frame-'+str(i).zfill(3)+'.jpg')
  if i<180:
   t=i/179.0;e=t*t*(3-2*t);pitch=-89.5*e;yaw=9.84*e;zoom=1-.55*e;dolly=1+3*e
  elif i<210:pitch=-89.5;yaw=9.84;zoom=.45;dolly=4
  else:
   t=(i-210)/89.0;e=t*t*(3-2*t);pitch=-89.5+59.59*e;yaw=9.84;zoom=.45+.35*e;dolly=4-3*e
  row.Camera.Yaw=yaw;row.Camera.Pitch=pitch;row.Camera.Zoom=zoom;WorkbenchService.ApplyCamera(D,row,vp,1920,1080)
  # Dolly the REAL perspective camera away while narrowing the REAL frustum.
  # Keep composition stable; no image scaling, forced plan mode or frame blending.
  p=vp.CameraLocation;back=vp.CameraZ;target=p-back*distance;position=target+back*(distance*dolly)
  cam=Rhino.DocObjects.ViewportInfo(vp);cam.SetCameraLocation(position)
  frustum=vp.GetFrustum();l,r,b,t,n,f=frustum[-6:];cam.SetFrustum(l/dolly,r/dolly,b/dolly,t/dolly,n,max(f,distance*dolly+200));vp.SetViewProjection(cam,True);cam.Dispose()
  bmp=view.CaptureToBitmap(System.Drawing.Size(1920,1080),mode.DisplayAttributes);bmp.Save(path,ImageFormat.Jpeg);bmp.Dispose()
  if i in [0,150,179,195,210,299]:
   entries=list(method.Invoke(None,System.Array[System.Object]([D,vp])));proof.append(dict(frame=i,plants=len(entries),plan=sum(e.Item2.IsPlan for e in entries),lifts=[round((e.Item2.Anchor.Z-e.Item2.GroundAnchor.Z)/e.Item2.TreeHeight,6) for e in entries if e.Item2.IsPlan],camera=[position.X,position.Y,position.Z],dolly=dolly))
  if i%15==0:json.dump(dict(frame=i,total=300),open(os.path.join(out,'progress.json'),'w'))
 json.dump(dict(frames=300,settings=dict(mode=settings.Mode,planAngle=settings.PlanAngle,planHeightRatio=settings.PlanHeightRatio),proof=proof,modelCalls=0),open(os.path.join(out,'capture.json'),'w'),indent=2)
 print(json.dumps(proof))
finally:
 vp.SetViewProjection(saved,True);D.Modified=modified;D.Views.Redraw()

"""B-only exact camera/resolution replay of the saved v0.5.0 direct-light export."""
import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin');clr.AddReference('RhinoSceneFlow.Core')
from RhinoSceneFlow.Plugin import McpApi
from RhinoSceneFlow.Core import ShadowSettings,ShadowVolumeRenderer,Vec3,Rgb,PsdWriter
from System.Reflection import BindingFlags
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'direct')
assert all(o.Attributes.GetUserString('SceneFlowShadowResearch')=='20261022' for o in doc.Objects)
with open(os.path.join(folder,'camera.json')) as f:data=json.load(f)
with open(os.path.join(folder,'benchmark-0.5.0.json')) as f:old=json.load(f)['result']
version=json.loads(McpApi.Execute('{"apiVersion":1,"operation":"describe"}'))['result']['version']
vp=Rhino.Display.RhinoViewport();vp.Size=System.Drawing.Size(*data['size'])
info=Rhino.DocObjects.ViewportInfo(vp)
info.SetCameraLocation(Rhino.Geometry.Point3d(*data['location']));info.SetCameraDirection(Rhino.Geometry.Vector3d(*data['direction']));info.SetCameraUp(Rhino.Geometry.Vector3d(*data['up']))
info.IsParallelProjection=data['parallel'];assert info.SetFrustum(*data['frustum']);assert vp.SetViewProjection(info,True)
token=System.Threading.CancellationToken(False);typ=clr.GetClrType(McpApi).Assembly.GetType('RhinoSceneFlow.Plugin.SceneReader')
watch=System.Diagnostics.Stopwatch.StartNew()
reader=System.Activator.CreateInstance(typ,BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Instance,None,System.Array[System.Object]([doc,vp,token,True,True]),None)
try:
 typ.GetProperty('VisibilityViewport').SetValue(reader,doc.Views.ActiveView.ActiveViewport)
 for t in typ.GetMethod('Read').Invoke(reader,None):pass
 world=typ.GetProperty('WorldTriangles').GetValue(reader);camera=typ.GetProperty('Camera').GetValue(reader)
 surfaces=typ.GetProperty('Surfaces').GetValue(reader);w=old['export']['width'];h=old['export']['height']
 settings=ShadowSettings(Vec3(*old['toSun']),Rgb(90,90,90),True,old['bias'],1)
 evaluate=surfaces.GetType().GetMethod('Evaluator').Invoke(surfaces,System.Array[System.Object]([camera,System.Int32(w),System.Int32(h),settings]))
 image=ShadowVolumeRenderer.Render(w,h,camera,world,settings,token,evaluate)
 path=os.path.join(folder,'benchmark-exact-'+version+'.psd');PsdWriter.Save(path,image,token,True,True)
 result=dict(pid=EXPECTED_PID,version=version,width=w,height=h,path=path,milliseconds=watch.ElapsedMilliseconds,queries=surfaces.GetType().GetProperty('Queries').GetValue(surfaces),triangles=world.Count,baselineMilliseconds=old['export']['elapsedMilliseconds'])
 with open(os.path.join(folder,'benchmark-exact-'+version+'.json'),'w') as f:json.dump(result,f,indent=2)
 print(json.dumps(result))
finally:
 reader.Dispose();vp.Dispose();info.Dispose()

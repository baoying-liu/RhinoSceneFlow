"""B-only native smooth/geometric receiver contact regression with full direct shadows."""
import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
from Rhino.Geometry import Point3d,BoundingBox
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;vp=doc.Views.ActiveView.ActiveViewport
assert all(o.Attributes.GetUserString('SceneFlowShadowResearch')=='20261022' for o in doc.Objects)
saved=Rhino.DocObjects.ViewportInfo(vp);modified=doc.Modified;results=[]
try:
 for label,x in [('smooth',100),('geometric',110)]:
  vp.SetProjection(Rhino.Display.DefinedViewportProjection.Top,'Direct_Gap',True)
  vp.ZoomBoundingBox(BoundingBox(Point3d(x-2,-2,0),Point3d(x+2,2,.25)))
  p=vp.WorldToClient(Point3d(x,0,0))
  path=os.path.join(OUTPUT_DIR,'direct','gap-'+label+'.psd')
  r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation='export_shadow_psd',document=int(doc.RuntimeSerialNumber),backend='volume',width=256,path=path,overwrite=True,toSun=[1,0,1]))))
  assert r['ok'] and r['result']['includeFormShading'],r
  e=r['result']['export'];results.append(dict(path=path,x=int(p.X*e['width']/vp.Size.Width),y=int(p.Y*e['height']/vp.Size.Height)))
finally:
 vp.SetViewProjection(saved,True);saved.Dispose();doc.Modified=modified
with open(os.path.join(OUTPUT_DIR,'direct','gaps.json'),'w') as f:json.dump(results,f,indent=2)
print(json.dumps(results))

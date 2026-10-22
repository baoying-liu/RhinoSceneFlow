"""Independent geometric-ray reference on the same Rhino meshing; B only."""
import clr,System,Rhino,os,json
clr.AddReference('RhinoSceneFlow.Plugin')
clr.AddReference('RhinoSceneFlow.Core')
from RhinoSceneFlow.Plugin import McpApi
from RhinoSceneFlow.Core import ShadowRenderer,ShadowSettings,WorldTriangle,Vec3,Rgb,PsdWriter
from Rhino.DocObjects import ViewportInfo
from Rhino.Geometry import Point3d,BoundingBox
from Rhino.Display import DefinedViewportProjection
from System.Collections.Generic import List
from System.Reflection import BindingFlags
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;vp=doc.Views.ActiveView.ActiveViewport
assert all(o.Attributes.GetUserString('SceneFlowShadowResearch')=='20261022' for o in doc.Objects)
saved=ViewportInfo(vp);modified=doc.Modified
try:
 vp.SetProjection(DefinedViewportProjection.Perspective,'Volume_Probe',True)
 vp.SetCameraLocations(Point3d(11,0,2),Point3d(45,-48,36));vp.ZoomBoundingBox(BoundingBox(Point3d(-11,-7,-2),Point3d(34,7,10)))
 typ=clr.GetClrType(McpApi).Assembly.GetType('RhinoSceneFlow.Plugin.SceneReader')
 token=System.Threading.CancellationToken(False)
 reader=System.Activator.CreateInstance(typ,BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Instance,None,System.Array[System.Object]([doc,vp,token,True,False]),None)
 for t in typ.GetMethod('Read').Invoke(reader,None):pass
 world=typ.GetProperty('WorldTriangles').GetValue(reader);camera=typ.GetProperty('Camera').GetValue(reader)
 geometry=List[WorldTriangle]()
 for t in world:geometry.Add(WorldTriangle(t.A,t.B,t.C))
 width=1024;height=int(round(width*float(vp.Size.Height)/vp.Size.Width))
 image=ShadowRenderer.Render(width,height,camera,geometry,ShadowSettings(Vec3(-.3,-1,1),Rgb(90,90,90),False,max(doc.ModelAbsoluteTolerance*.001,1e-7),1),token)
 path=os.path.join(OUTPUT_DIR,'volumes-v041','geometric-ray-perspective.psd')
 PsdWriter.Save(path,image,token,True,True)
 print(json.dumps(dict(path=path,triangles=geometry.Count)))
finally:
 vp.SetViewProjection(saved,True);saved.Dispose();doc.Modified=modified

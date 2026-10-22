"""B-only counterexample: smooth vertex normals must not erase a nearby cast shadow."""
import clr,Rhino,System,os,json
from Rhino.Geometry import Mesh,Point3d,BoundingBox,Vector3d
from Rhino.DocObjects import ObjectAttributes,ViewportInfo
from Rhino.Display import DefinedViewportProjection
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;vp=doc.Views.ActiveView.ActiveViewport
assert all(o.Attributes.GetUserString('SceneFlowShadowResearch')=='20261022' for o in doc.Objects)
folder=os.path.join(OUTPUT_DIR,'alternatives');cases=[];saved=ViewportInfo(vp)
def add_mesh(name,corners,normals):
    existing=next((o for o in doc.Objects if o.Attributes.Name==name),None)
    if existing:return existing.Id
    m=Mesh()
    for p in corners:m.Vertices.Add(*p)
    m.Faces.AddFace(0,1,2,3)
    for xyz in normals:
        n=Vector3d(*xyz);n.Unitize();m.Normals.Add(n.X,n.Y,n.Z)
    a=ObjectAttributes();a.Name=name;a.SetUserString('SceneFlowShadowResearch','20261022')
    return doc.Objects.AddMesh(m,a)
try:
 for name,x,smooth in [('smooth-receiver',100,True),('geometric-receiver',110,False)]:
    corners=[(x-2,-2,0),(x+2,-2,0),(x+2,2,0),(x-2,2,0)]
    normals=[(-.3,-.3,1),(.3,-.3,1),(.3,.3,1),(-.3,.3,1)] if smooth else [(0,0,1)]*4
    add_mesh('Counterexample_'+name,corners,normals)
    add_mesh('Counterexample_Roof_'+name,[(x+.15,-.5,.25),(x+.35,-.5,.25),(x+.35,.5,.25),(x+.15,.5,.25)],[(0,0,1)]*4)
    vp.SetProjection(DefinedViewportProjection.Top,'Shadow_Counterexample',True)
    vp.ZoomBoundingBox(BoundingBox(Point3d(x-2,-2,0),Point3d(x+2,2,.25)))
    path=os.path.join(folder,'contact-'+name+'.psd')
    result=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation='export_shadow_psd',document=int(doc.RuntimeSerialNumber),width=1024,path=path,overwrite=True,toSun=[1,0,1]))))
    assert result['ok'],result
    point=vp.WorldToClient(Point3d(x,0,0));data=result['result']['export']
    roof=[vp.WorldToClient(Point3d(x+dx,dy,.25)) for dx,dy in [(.15,-.5),(.35,.5)]]
    roof_rect=[roof[0].X*data['width']/vp.Size.Width,roof[1].Y*data['height']/vp.Size.Height,roof[1].X*data['width']/vp.Size.Width,roof[0].Y*data['height']/vp.Size.Height]
    cases.append(dict(name=name,export=data,roofRect=roof_rect,probe=[int(point.X*data['width']/vp.Size.Width),int(point.Y*data['height']/vp.Size.Height)],expectedAlpha=255,
      reason='Ray from (x,0,0) toward (1,0,1) intersects roof at (x+0.25,0,0.25), strictly inside [x+0.15,x+0.35] x [-0.5,0.5]. Receiver geometry and roof dimensions are identical; only vertex normals differ.'))
finally:vp.SetViewProjection(saved,False)
with open(os.path.join(folder,'contact-counterexample.json'),'w') as f:json.dump({'pid':EXPECTED_PID,'cases':cases},f,indent=2)
print(json.dumps(cases))

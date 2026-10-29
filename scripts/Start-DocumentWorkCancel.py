"""Close an owned B fixture immediately after starting the real external xatlas worker."""
import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'document-switch')
assert doc.Path.lower().endswith('owned-open.3dm'),doc.Path
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
mesh=Rhino.Geometry.Mesh.CreateFromSphere(Rhino.Geometry.Sphere(Rhino.Geometry.Point3d.Origin,100),120,80)
oid=doc.Objects.AddMesh(mesh);mesh.Dispose()
job=api('material_unwrap_start',objects=[str(oid)])
with open(os.path.join(folder,'cancel-start.json'),'w') as f:json.dump(dict(pid=EXPECTED_PID,document=int(doc.RuntimeSerialNumber),job=job['id']),f,indent=2)
doc.Modified=False
assert Rhino.RhinoApp.RunScript('_-New _None',False)
print(json.dumps(dict(pid=EXPECTED_PID,job=job['id'],newCommandCompleted=True)))

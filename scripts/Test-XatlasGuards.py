import Rhino,System,clr,json,os
from Rhino.Geometry import Transform,Vector3d
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'xatlas');s=json.load(open(os.path.join(folder,'start.json')))
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))));assert r['ok'],r;return r['result']
source=doc.Objects.FindId(System.Guid(s['objects'][0]['id']));mesh=source.Geometry.Duplicate();attrs=Rhino.DocObjects.ObjectAttributes();attrs.Name='xatlas stale guard fixture';attrs.LayerIndex=source.Attributes.LayerIndex
id=doc.Objects.Add(mesh,attrs);mesh.Dispose()
job=api('material_unwrap_start',objects=[str(id)])
changed=doc.Objects.FindId(id).Geometry.Duplicate();changed.Transform(Transform.Translation(Vector3d(1000,0,0)));assert doc.Objects.Replace(id,changed);changed.Dispose()
with open(os.path.join(folder,'guard-start.json'),'w') as f:json.dump(dict(job=job,object=str(id),pid=EXPECTED_PID),f)
print(json.dumps(job))

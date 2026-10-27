import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'xatlas');s=json.load(open(os.path.join(folder,'guard-start.json')))
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))));assert r['ok'],r;return r['result']
job=api('material_unwrap_status',jobId=s['job']['id']);assert job['status']=='failed',job
o=doc.Objects.FindId(System.Guid(s['object']));assert o.Attributes.GetUserString('RhinoSceneFlow.WorldUv') is None
cancel=api('material_unwrap_start',objects=[s['object']]);api('material_unwrap_cancel',jobId=cancel['id'])
s.update(staleResult=job,cancel=cancel)
with open(os.path.join(folder,'guard-cancel.json'),'w') as f:json.dump(s,f)
print(json.dumps(s))

"""Check the worker cancelled and no old result crossed into the new document."""
import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
folder=os.path.join(OUTPUT_DIR,'document-switch');before=json.load(open(os.path.join(folder,'cancel-start.json')))
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,**kw))))
 assert r['ok'],r
 return r['result']
doc=__rhino_doc__;assert int(doc.RuntimeSerialNumber)!=before['document'] and doc.Objects.Count==0
job=api('material_unwrap_status',jobId=before['job']);assert job['status']=='cancelled',job
s=api('material_workspace_status');assert all(v['document']==int(doc.RuntimeSerialNumber) and v['error'] is None for v in s['tools'].values()),s
report=dict(pid=EXPECTED_PID,oldDocument=before['document'],document=int(doc.RuntimeSerialNumber),job=job,emptyNewDocument=True,allToolsRebound=True)
with open(os.path.join(folder,'cancel-verified.json'),'w') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(pid=EXPECTED_PID,workerCancelled=True,emptyNewDocument=True,allToolsRebound=True)))

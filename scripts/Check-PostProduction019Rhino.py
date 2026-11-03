import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
folder=os.path.join(OUTPUT_DIR,'postproduction019');record=json.load(open(os.path.join(folder,'bridge.json')))
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,**kw))));assert r['ok'],r;return r['result']
job=api('postproduction_status',jobId=record['job']);assert job['status']=='completed',job
assert job['response']['version']=='0.19.0' and job['response']['generationAvailable']
doc=__rhino_doc__;assert (doc.Objects.Count,doc.Modified)==(record['objects'],record['modified'])
ws=api('material_workspace_status');assert all(t['error'] is None for t in ws['tools'].values())
json.dump(dict(pid=EXPECTED_PID,service=job['response'],objectsUnchanged=True,allToolsHealthy=True),open(os.path.join(folder,'bridge-verified.json'),'w'),indent=2)
print(json.dumps(dict(pid=EXPECTED_PID,bridge=True,objectsUnchanged=True)))

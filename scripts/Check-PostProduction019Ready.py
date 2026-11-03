import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
folder=os.path.join(OUTPUT_DIR,'postproduction019');record=json.load(open(os.path.join(folder,'before.json')))
doc=__rhino_doc__;assert doc.Path==record['path'] and not doc.Modified and doc.Objects.Count==record['objects']
for ident in record['selection']:doc.Objects.Select(System.Guid(ident))
r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation='material_workspace_status'))));assert r['ok'] and all(t['error'] is None for t in r['result']['tools'].values()),r
job=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation='postproduction_start',document=int(doc.RuntimeSerialNumber),browser=False))));assert job['ok'],job
json.dump(dict(pid=EXPECTED_PID,path=doc.Path,objects=doc.Objects.Count,modified=doc.Modified,webLaunch=job['result']['id'],allToolsHealthy=True),open(os.path.join(folder,'ready.json'),'w'),indent=2)
print(json.dumps(dict(pid=EXPECTED_PID,restored=True,objects=doc.Objects.Count,modified=doc.Modified)))

import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
folder=os.path.join(OUTPUT_DIR,'postproduction019');record=json.load(open(os.path.join(folder,'bridge-post.json')))
r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation='postproduction_status',jobId=record['job']))));assert r['ok'],r
job=r['result'];assert job['status']=='completed',job
doc=__rhino_doc__;assert (doc.Objects.Count,doc.Modified)==(record['objects'],record['modified'])
json.dump(dict(pid=EXPECTED_PID,webJob=job['response']['job'],run=job['response']['run'],postBridge=True,objectsUnchanged=True),open(os.path.join(folder,'bridge-post-response.json'),'w'),indent=2)
print(json.dumps(dict(postBridge=True,webJob=job['response']['job'])))

"""Exercise POST through the original Platform bridge by re-fusing an accepted example (zero image calls)."""
import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
folder=os.path.join(OUTPUT_DIR,'postproduction019');stage=json.load(open(os.path.join(folder,'staged.json')))
doc=__rhino_doc__;before=(doc.Objects.Count,doc.Modified)
r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation='postproduction_request',method='POST',route='/api/projects/'+stage['exampleProject']+'/runs/'+stage['exampleRun']+'/resume',body={}))));assert r['ok'],r
json.dump(dict(job=r['result']['id'],objects=before[0],modified=before[1]),open(os.path.join(folder,'bridge-post.json'),'w'))
assert (doc.Objects.Count,doc.Modified)==before
print(json.dumps(dict(postJob=r['result']['id'])))

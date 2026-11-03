import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.abspath(os.path.join(OUTPUT_DIR,'..','examples','Hillside-Retreat'))
request=dict(apiVersion=1,operation='material_chat_status',jobId=json.load(open(os.path.join(folder,'tree-job.json')))['id'])
reply=json.loads(McpApi.Execute(json.dumps(request)));assert reply['ok'],reply;job=reply['result']
with open(os.path.join(folder,'tree-state.json'),'w') as f:json.dump(job,f,indent=2)
print(json.dumps(dict(status=job['status'],stage=job['stage'],plant=job['plant'],matches=job['plantMatches'],error=job['error'])))

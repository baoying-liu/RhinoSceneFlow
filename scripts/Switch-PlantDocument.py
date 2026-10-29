import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
folder=os.path.join(OUTPUT_DIR,'plants015');setup=json.load(open(os.path.join(folder,'cancel-ui-start.json')))
state=json.loads(McpApi.Execute('{"apiVersion":1,"operation":"material_quick_status"}'))['result'];job=state['lastJob']
if not job or job==setup['before']:print('Waiting for ChatKit dispatch')
else:
 result=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation='material_chat_status',jobId=job))))['result'];assert result['status']=='running',result
 setup['job']=job
 with open(os.path.join(folder,'cancel-ui-start.json'),'w') as f:json.dump(setup,f)
 assert __rhino_doc__.Objects.Count==0 and not __rhino_doc__.Modified
 assert Rhino.RhinoApp.RunScript('_-New _None',False)

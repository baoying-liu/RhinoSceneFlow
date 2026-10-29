import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
folder=os.path.join(OUTPUT_DIR,'random014');setup=json.load(open(os.path.join(folder,'setup.json')))
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(__rhino_doc__.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
report=dict(chat=api('material_chat_status',jobId=setup['aiJob']))
task=System.AppDomain.CurrentDomain.GetData('Random014BrickAi')
report['brickCompleted']=task is not None and task.IsCompleted
if report['brickCompleted']:
 from RhinoSceneFlow.Core import MaterialLibrary
 report['brick']=json.loads(System.Text.Json.JsonSerializer.Serialize(task.Result,task.Result.GetType(),MaterialLibrary.Json))
report['library']=api('material_library')
with open(os.path.join(folder,'ai-status.json'),'w') as f:json.dump(report,f,indent=2)
print(json.dumps(report))

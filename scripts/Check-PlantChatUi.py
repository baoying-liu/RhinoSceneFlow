import Rhino,System,clr,json,os
from System.Reflection import BindingFlags
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
folder=os.path.join(OUTPUT_DIR,'plants015');task=System.AppDomain.CurrentDomain.GetData('PlantChatUiProbe');assert task is not None and task.IsCompleted
probe=json.loads(json.loads(task.Result));assert probe.get('ready') and not probe.get('error'),probe
r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation='material_quick_status',document=int(__rhino_doc__.RuntimeSerialNumber)))));assert r['ok'];state=r['result']
job=state.get('lastJob')
if not job:print('ChatKit message not dispatched yet')
else:
 result=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation='material_chat_status',jobId=job))));assert result['ok'];job=result['result']
 if job['status']=='running':print(json.dumps(dict(status=job['status'],stage=job['stage'])))
 else:
  assert job['status']=='completed' and job['kind']=='plant' and not job['imagePath'],job
  workspace=json.loads(McpApi.Execute('{"apiVersion":1,"operation":"material_workspace_status"}'))['result'];panel=Rhino.UI.Panels.GetPanel(System.Guid(workspace['pages'][0]['panelId']));flags=BindingFlags.Instance|BindingFlags.NonPublic|BindingFlags.Public
  tool=panel.GetType().GetProperty('Tool',flags).GetValue(panel);button=tool.GetType().GetField('apply',flags).GetValue(tool);scope=tool.GetType().GetField('scope',flags).GetValue(tool)
  assert button.Text=='打开植物库与种植' and not scope.Visible
  with open(os.path.join(folder,'chat-ui-verified.json'),'w') as f:json.dump(dict(pid=EXPECTED_PID,realChatKitMessage=True,job=job,plantButton=True,materialControlsHidden=True),f,indent=2)
  print('Existing ChatKit -> plant reply -> plant controls verified without OS input')

"""Verify early-startup close performed both transitions and rebound without errors."""
import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
folder=os.path.join(OUTPUT_DIR,'document-switch');before=json.load(open(os.path.join(folder,'startup-close.json')))
serial=int(__rhino_doc__.RuntimeSerialNumber);assert serial!=before['middle'] and before['middle']!=before['before']
assert before['chat']!='ready',before
r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation='material_workspace_status'))));assert r['ok'],r
assert all(t['error'] is None and t['document']==serial for t in r['result']['tools'].values()),r
report=dict(pid=EXPECTED_PID,before=before,document=serial,allToolsRebound=True)
with open(os.path.join(folder,'startup-close-verified.json'),'w') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(pid=EXPECTED_PID,closedBeforeChatReady=True,twoTransitions=True,allToolsRebound=True)))

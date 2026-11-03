"""Save through Rhino's native Save command; only operates on the owned demo path."""
import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.abspath(os.path.join(OUTPUT_DIR,'..','examples','Hillside-Retreat'));model=json.load(open(os.path.join(folder,'views.json')))['model']
assert doc.Path==model,(doc.Path,model)
doc.Views.ActiveView.Maximized=True
assert Rhino.RhinoApp.RunScript('_-Save _Enter',False)
assert not doc.Modified,'Native Save did not finish'
r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation='plant_group_state',document=int(doc.RuntimeSerialNumber),groupId=json.load(open(os.path.join(folder,'planting.json')))['group']))));assert r['ok'],r
state=r['result'];report=dict(model=model,pid=EXPECTED_PID,bytes=os.path.getsize(model),count=state['count'],manual=state['manual'],busy=state['busy'],modified=doc.Modified)
with open(os.path.join(folder,'checkpoint.json'),'w') as f:json.dump(report,f,indent=2)
print(json.dumps(report))

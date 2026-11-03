import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'properties017');before=json.load(open(os.path.join(folder,'new-before.json')))
assert EXPECTED_PID==before['pid'] and int(doc.RuntimeSerialNumber)!=before['document'] and doc.Objects.Count==0 and not doc.Modified
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
assert api('describe')['version']=='0.17.0'
for page in ['materials','library','uv','planting','export','plantsList','properties']:api('material_workspace_open',page=page)
state=api('material_workspace_status');assert len(state['pages'])==7 and len(state['tools'])==7 and all(t['error'] is None and t['document']==int(doc.RuntimeSerialNumber) for t in state['tools'].values()),state
assert api('material_library')['directory']==before['restoredLibrary']
assert api('plant_group_list')['groups']==[] and api('plant_edit_status')['group'] is None
with open(os.path.join(folder,'ready.json'),'w') as f:json.dump(dict(pid=EXPECTED_PID,document=int(doc.RuntimeSerialNumber),version='0.17.0',newDocumentRebound=True,libraryRestored=True,workspace=state),f,indent=2)
print(json.dumps(dict(pid=EXPECTED_PID,version='0.17.0',tools=7,nativeNewPassed=True,libraryRestored=True)))

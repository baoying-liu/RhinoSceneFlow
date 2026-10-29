import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
folder=os.path.join(OUTPUT_DIR,'random014');setup=json.load(open(os.path.join(folder,'setup.json')))
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(__rhino_doc__.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
assert api('describe')['version']=='0.14.0'
assert api('material_library')['directory']==setup['originalLibrary']
state=api('material_workspace_group');assert all(t['error'] is None for t in state['tools'].values())
with open(os.path.join(folder,'restart-ready.json'),'w') as f:json.dump(dict(pid=EXPECTED_PID,version='0.14.0',allToolsHealthy=True,originalLibraryRestored=True),f,indent=2)
print('Restarted final B version ready; original material library preserved')

"""Post-restart public API smoke, without creating geometry or requesting images."""
import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,**kw))))
 assert r['ok'],r
 return r['result']
assert api('describe')['version']=='0.13.3'
state=api('material_workspace_open',page='library');assert len(state['pages'])==5
assets=api('material_library')['assets'];assert assets
selected=api('material_tool_select',page='library',assetId=assets[-1]['id'])
assert selected['chatKit'] is None and selected['shelf'] is not None
report=dict(pid=EXPECTED_PID,version='0.13.3',independentLibraryReady=True,workspace=api('material_workspace_status'))
with open(os.path.join(OUTPUT_DIR,'library0131','ready.json'),'w') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(pid=EXPECTED_PID,version='0.13.3',independentLibraryReady=True)))

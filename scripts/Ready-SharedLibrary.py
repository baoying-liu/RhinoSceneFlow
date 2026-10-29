"""Confirm original B catalog restored and chat/document sessions are isolated."""
import Rhino,System,clr,json,os
from System.Reflection import BindingFlags
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
folder=os.path.join(OUTPUT_DIR,'shared-library0133');setup=json.load(open(os.path.join(folder,'setup.json')))
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,**kw))))
 assert r['ok'],r
 return r['result']
assert api('describe')['version']=='0.13.3'
catalog=api('material_library');assert catalog['directory']==setup['originalLibrary']
s=api('material_workspace_group');serial=int(__rhino_doc__.RuntimeSerialNumber)
assert all(t['document']==serial and t['error'] is None for t in s['tools'].values()),s
panel=Rhino.UI.Panels.GetPanel(System.Guid(s['pages'][0]['panelId']))
tool=panel.GetType().GetProperty('Tool',BindingFlags.Instance|BindingFlags.NonPublic).GetValue(panel)
field=lambda o,n:o.GetType().GetField(n,BindingFlags.Instance|BindingFlags.NonPublic).GetValue(o)
data=field(field(field(tool,'chat'),'host'),'data');old=json.load(open(os.path.join(folder,'verified.json')))['chatData']
assert data!=old and str(EXPECTED_PID) in data and ('doc-'+str(serial)) in data
report=dict(pid=EXPECTED_PID,version='0.13.3',originalLibraryRestored=True,library=catalog['directory'],assetCount=len(catalog['assets']),chatData=data,chatSessionIsolated=True,allToolsHealthy=True)
with open(os.path.join(folder,'ready.json'),'w') as f:json.dump(report,f,indent=2)
print(json.dumps(report))

"""Check the catalog survived document replacement, then restore the B user's original root."""
import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
folder=os.path.join(OUTPUT_DIR,'shared-library0133');before=json.load(open(os.path.join(folder,'before-new.json')));setup=json.load(open(os.path.join(folder,'setup.json')))
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,**kw))))
 assert r['ok'],r
 return r['result']
assert int(__rhino_doc__.RuntimeSerialNumber)!=before['document'] and __rhino_doc__.Objects.Count==0
library=api('material_library');assert library['directory']==before['library'] and set(a['id'] for a in library['assets'])==set(before['assets'])
s=api('material_workspace_status');assert all(t['error'] is None and t['document']==int(__rhino_doc__.RuntimeSerialNumber) for t in s['tools'].values()),s
with open(os.path.join(folder,'cross-document.json'),'w') as f:json.dump(dict(pid=EXPECTED_PID,sharedLibraryPreserved=True,assetCount=len(library['assets']),newDocument=int(__rhino_doc__.RuntimeSerialNumber)),f,indent=2)
api('material_configure',directory=setup['originalLibrary'])
__rhino_doc__.Modified=False
assert Rhino.RhinoApp.RunScript('_-New _None',False)

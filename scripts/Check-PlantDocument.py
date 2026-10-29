import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
folder=os.path.join(OUTPUT_DIR,'plants015');setup=json.load(open(os.path.join(folder,'setup.json')));before=json.load(open(os.path.join(folder,'cancel-ui-start.json')))
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(__rhino_doc__.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
serial=int(__rhino_doc__.RuntimeSerialNumber);assert serial!=before['document']
job=api('material_chat_status',jobId=before['job']);assert job['status']=='cancelled',job
state=api('material_workspace_status');assert all(t['error'] is None and t['document']==serial for t in state['tools'].values()),state
assert len(api('plant_library')['assets'])==3
api('material_configure',directory=setup['originalLibrary']);api('plant_settings',settings=setup['oldSettings'])
with open(os.path.join(folder,'document-verified.json'),'w') as f:json.dump(dict(pid=EXPECTED_PID,document=serial,realChatKitCancelledOnNew=True,allToolsHealthy=True,noNewPlantImported=True,originalLibraryRestored=True),f,indent=2)
print('Native New cancelled the real ChatKit job; five tools healthy; no plant imported; library restored')

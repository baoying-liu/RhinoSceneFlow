import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__
record=json.load(open(os.path.join(OUTPUT_DIR,'postproduction018','launch.json')))
assert int(doc.RuntimeSerialNumber)!=record['before']['serial']
response=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation='material_workspace_status'))));assert response['ok'],response
assert all(t['error'] is None for t in response['result']['tools'].values())
assert response['result']['tools']['post']['document']==int(doc.RuntimeSerialNumber)
json.dump(dict(pid=EXPECTED_PID,newDocument=int(doc.RuntimeSerialNumber),previousDocument=record['before']['serial'],panelHealthy=True),open(os.path.join(OUTPUT_DIR,'postproduction018','new.json'),'w'),indent=2)
print('New document rebound postproduction tool without errors')

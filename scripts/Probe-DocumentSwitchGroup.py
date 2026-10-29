"""Open every SceneFlow tool before a native New/Open document command."""
import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation='material_workspace_group'))));assert r['ok'],r
print(json.dumps(dict(pid=EXPECTED_PID,document=int(__rhino_doc__.RuntimeSerialNumber),pages=len(r['result']['pages']))))

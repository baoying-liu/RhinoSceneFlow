"""Native New from our empty B fixture only. Independent Web service must survive."""
import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__
record=json.load(open(os.path.join(OUTPUT_DIR,'postproduction018','launch.json')))
assert doc.Objects.Count==0 and not doc.Modified and doc.Path is None
assert int(doc.RuntimeSerialNumber)==record['before']['serial']
assert Rhino.RhinoApp.RunScript('_-New _None',False)
print('Native New requested on owned empty B fixture')

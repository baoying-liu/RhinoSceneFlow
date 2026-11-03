"""Read-only B document receipt before managed update; no save or geometry mutations."""
import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__
folder=os.path.join(OUTPUT_DIR,'postproduction019');os.makedirs(folder,exist_ok=True)
api=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation='plant_edit_status'))))
json.dump(dict(pid=EXPECTED_PID,path=doc.Path,modified=doc.Modified,objects=doc.Objects.Count,
 document=int(doc.RuntimeSerialNumber),editing=api.get('result'),selection=[str(o.Id) for o in doc.Objects.GetSelectedObjects(False,False)]),
 open(os.path.join(folder,'before.json'),'w'),indent=2)
print(json.dumps(dict(path=doc.Path,modified=doc.Modified,objects=doc.Objects.Count)))

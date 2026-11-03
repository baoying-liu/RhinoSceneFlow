"""B-only public Platform entry. No geometry changes, no browser/mouse input."""
import clr, json, os, Rhino, System
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id == EXPECTED_PID
doc=__rhino_doc__
folder=os.path.join(OUTPUT_DIR,'postproduction018');os.makedirs(folder,exist_ok=True)
def api(op,**kw):
    result=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
    assert result['ok'],result
    return result['result']
assert api('describe')['version']=='0.18.0'
before=dict(serial=int(doc.RuntimeSerialNumber),objects=doc.Objects.Count,modified=doc.Modified,path=doc.Path)
api('material_workspace_open',page='post')
workspace=api('material_workspace_status');assert workspace['tools']['post']['error'] is None
path=os.path.abspath(os.path.join(OUTPUT_DIR,'..','examples','Hillside-Retreat','PSD','01 Hillside Axon.psd'))
assert os.path.isfile(path),path
job=api('postproduction_start',path=path,browser=False)
json.dump(dict(job=job['id'],before=before,psd=path),open(os.path.join(folder,'launch.json'),'w'),indent=2)
assert doc.Objects.Count==before['objects'] and doc.Modified==before['modified']
print(json.dumps(dict(job=job['id'],panel=True,objectsUnchanged=True)))

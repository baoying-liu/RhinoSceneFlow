import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
folder=os.path.join(OUTPUT_DIR,'plants015');setup=json.load(open(os.path.join(folder,'setup.json')));verified=json.load(open(os.path.join(folder,'ai-verified.json')))
assert __rhino_doc__.Objects.Count==0 and not __rhino_doc__.Modified
r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation='material_configure',directory=setup['library']))));assert r['ok'],r
assert Rhino.RhinoApp.RunScript('_-Open "'+verified['model']+'" _Enter',False)

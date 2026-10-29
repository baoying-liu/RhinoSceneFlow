import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
folder=os.path.join(OUTPUT_DIR,'random014');setup=json.load(open(os.path.join(folder,'setup.json')));ai=json.load(open(os.path.join(folder,'ai-status.json')))
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(__rhino_doc__.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
assert __rhino_doc__.Objects.Count==0 and not __rhino_doc__.Modified
api('material_configure',directory=setup['library'])
job=api('material_random_prepare',assetId=ai['chat']['material'],preview=True)
with open(os.path.join(folder,'new-start.json'),'w') as f:json.dump(dict(pid=EXPECTED_PID,document=int(__rhino_doc__.RuntimeSerialNumber),job=job['id']),f)
assert Rhino.RhinoApp.RunScript('_-New _None',False)

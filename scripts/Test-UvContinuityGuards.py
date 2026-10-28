import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'uv-v012');s=json.load(open(os.path.join(folder,'ready.json')))
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))));assert r['ok'],r;return r['result']
target=s['ids'][1];s['beforeUv']=api('material_uv_status',objects=[target]);s['cancelJob']=api('material_unwrap_start',objects=[target],method='tube',guideId=s['guide']);api('material_unwrap_cancel',jobId=s['cancelJob']['id'])
with open(os.path.join(folder,'guard-cancel.json'),'w') as f:json.dump(s,f)
print('Cancelled a real tube worker')

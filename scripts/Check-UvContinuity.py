import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi,SceneFlowPlugin
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'uv-v012');s=json.load(open(os.path.join(folder,'start.json')))
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))));assert r['ok'],r;return r['result']
j=api('material_unwrap_status',jobId=s['job']['id']);assert j['status']=='completed',j
api('material_apply',assetId=s['asset'],objects=[s['ids'][0],s['ids'][2]])
print(json.dumps(j));print(json.dumps(api('material_uv_renderer')))
proof=[]
for id in [s['ids'][0],s['ids'][2]]:
 row=api('material_uv_renderer',objectId=id);assert len(row['primitives'])==1 and all(p['uvError']<1e-6 and p['normalError']<1e-6 and p['volume']>0 for p in row['primitives']),row
 proof.append(row)
s['rendererProof']=proof
# Reserve an unrelated high channel: the plugin must not overwrite it.
reserved=Rhino.Render.TextureMapping.CreatePlaneMapping(Rhino.Geometry.Plane.WorldXY,Rhino.Geometry.Interval(0,1000),Rhino.Geometry.Interval(0,1000),Rhino.Geometry.Interval(-1,1))
assert doc.Objects.FindId(System.Guid(s['ids'][1])).SetTextureMapping(1000,reserved);reserved.Dispose()
tube=api('material_unwrap_start',objects=[s['ids'][1]],method='tube',guideId=s['guide']);s['tubeJob']=tube;s['xatlasResult']=j
with open(os.path.join(folder,'tube-start.json'),'w') as f:json.dump(s,f,indent=2)
print(json.dumps(tube))

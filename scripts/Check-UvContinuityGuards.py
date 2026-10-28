import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'uv-v012');s=json.load(open(os.path.join(folder,'guard-cancel.json')))
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))));assert r['ok'],r;return r['result']
assert api('material_unwrap_status',jobId=s['cancelJob']['id'])['status']=='cancelled'
assert api('material_uv_status',objects=[s['ids'][1]])==s['beforeUv']
doc.Objects.Show(System.Guid(s['guide']),True)
guide=doc.Objects.FindId(System.Guid(s['guide']));original=guide.Geometry.DuplicateCurve();System.AppDomain.CurrentDomain.SetData('SceneFlow.Uv.GuideBackup',original)
s['staleJob']=api('material_unwrap_start',objects=[s['ids'][1]],method='tube',guideId=s['guide']);moved=original.DuplicateCurve();moved.Transform(Rhino.Geometry.Transform.Translation(10,0,0));assert doc.Objects.Replace(guide.Id,moved),"Guide replacement failed";moved.Dispose();doc.Objects.Hide(guide.Id,True)
with open(os.path.join(folder,'guard-stale.json'),'w') as f:json.dump(s,f)
print('Changed guide during a real worker; waiting for stale-result rejection')

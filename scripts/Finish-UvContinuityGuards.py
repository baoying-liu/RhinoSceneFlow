import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'uv-v012');s=json.load(open(os.path.join(folder,'guard-stale.json')))
def raw(op,**kw):return json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
def api(op,**kw):
 r=raw(op,**kw);assert r['ok'],r;return r['result']
assert api('material_unwrap_status',jobId=s['staleJob']['id'])['status']=='failed'
doc.Objects.Show(System.Guid(s['guide']),True)
original=System.AppDomain.CurrentDomain.GetData('SceneFlow.Uv.GuideBackup');assert doc.Objects.Replace(System.Guid(s['guide']),original);original.Dispose();System.AppDomain.CurrentDomain.SetData('SceneFlow.Uv.GuideBackup',None);doc.Objects.Hide(System.Guid(s['guide']),True)
target=s['ids'][1];assert api('material_uv_status',objects=[target])==s['beforeUv']
obj=doc.Objects.FindId(System.Guid(target));record=s['beforeUv'][0]['status']['record'];channel=record['meshChannel'];assert channel!=1000
previous=obj.GetTextureMapping(channel);changed=doc.Objects.FindId(obj.Id).GetTextureMapping(channel);changed.UvwTransform=Rhino.Geometry.Transform.Translation(.1,0,0);assert obj.SetTextureMapping(channel,changed);changed.Dispose()
assert not api('material_uv_status',objects=[target])[0]['status']['valid'];assert not raw('material_uv_renderer',objectId=target)['ok']
assert obj.SetTextureMapping(channel,previous);previous.Dispose();assert api('material_uv_status',objects=[target])[0]['status']['valid']
api('material_uv_renderer',objectId=target)
api('material_restore',objects=[target]);obj=doc.Objects.FindId(System.Guid(target));assert obj.GetTextureMapping(channel) is None
reserved=obj.GetTextureMapping(1000);assert reserved is not None;reserved.Dispose();assert obj.Attributes.GetUserString('RhinoSceneFlow.WorldUv') is None
s['rebuildJob']=api('material_unwrap_start',objects=[target],method='tube',guideId=s['guide'])
s.update(cancelPassed=True,guideStalePassed=True,mappingStalePassed=True,unrelatedChannelPreserved=True,restorePassed=True)
with open(os.path.join(folder,'guards-rebuild.json'),'w') as f:json.dump(s,f,indent=2)
print('PASS: cancel, stale guide, stale mapping, restore and unrelated channel; rebuilding final test surface')

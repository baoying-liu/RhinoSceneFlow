import Rhino,System,clr,json,os
from System.Reflection import BindingFlags
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import MaterialQuickController,MaterialPanelController,McpApi
D=__rhino_doc__;ready=json.load(open(os.path.join(OUTPUT_DIR,'materials','demo','ready.json')))
p=MaterialQuickController.Open(D,System.Array[System.Guid]([System.Guid(ready['objects'][1])]))
p.SelectAsset(System.Guid(ready['ai']['id']))
old=MaterialPanelController.Find(D.RuntimeSerialNumber)
if old is not None:old.Close()
flags=BindingFlags.Instance|BindingFlags.NonPublic
# Cancel before the first UV step: no mapping or material change.
before=D.Objects.FindId(System.Guid(ready['objects'][1])).Attributes.GetUserString('RhinoSceneFlow.WorldUv')
p.GetType().GetMethod('Start',flags).Invoke(p,System.Array[System.Object]([False]));assert p.Busy
p.GetType().GetMethod('Cancel',flags).Invoke(p,None);assert not p.Busy
assert before==D.Objects.FindId(System.Guid(ready['objects'][1])).Attributes.GetUserString('RhinoSceneFlow.WorldUv')
refs=p.GetType().GetField('references',flags).GetValue(p);refs.Add(os.path.join(ready['library'],'assets',ready['ai']['id'].replace('-',''),ready['ai']['maps']['baseColor']))
p.GetType().GetMethod('RefreshReferences',flags).Invoke(p,None)
p.GetType().GetMethod('Generate',flags).Invoke(p,None)
r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation='material_quick_status',document=int(D.RuntimeSerialNumber)))))['result'];assert r['jobId'] is not None,r
job=r['jobId']
r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation='material_generation_progress',jobId=job,stage='Reading reference image'))));assert r['ok'],r
with open(os.path.join(OUTPUT_DIR,'worlduv','quick-generation.json'),'w') as f:json.dump(dict(jobId=job,oldSelected=ready['ai']['id'],cancelBeforeFirstStep=True),f)
print(json.dumps(dict(jobId=job,cancelBeforeFirstStep=True)))

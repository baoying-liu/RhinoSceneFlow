"""Real UI Generate button -> local Codex -> new image -> library, with reference image."""
import Rhino,System,clr,json,os
from System.Reflection import BindingFlags
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi,MaterialQuickController
D=__rhino_doc__;assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
folder=os.path.join(OUTPUT_DIR,'materials-v09');os.makedirs(folder,exist_ok=True)
ready=json.load(open(os.path.join(OUTPUT_DIR,'materials','demo','ready.json')))
p=MaterialQuickController.Open(D,System.Array[System.Guid]([System.Guid(ready['objects'][1])]))
flags=BindingFlags.Instance|BindingFlags.NonPublic
p.GetType().GetField('prompt',flags).GetValue(p).Text='中灰色清水混凝土，细小均匀气孔，无接缝，整张贴图代表 1×1 米。参考图片的质感，颜色稍深。'
ref=os.path.abspath(os.path.join(OUTPUT_DIR,'..','materials','source','ai-concrete-20261027-92620a53.png'))
p.GetType().GetField('references',flags).GetValue(p).Add(ref)
p.GetType().GetMethod('RefreshReferences',flags).Invoke(p,None)
p.GetType().GetMethod('Generate',flags).Invoke(p,None)
def api(op):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(D.RuntimeSerialNumber)))));assert r['ok'],r
 return r['result']
state=api('material_quick_status');assert state['jobId'],state
job=next(j for j in api('material_generation_jobs') if j['id']==state['jobId']);assert job['executor']=='codex-local' and job['status']=='running',job
assert not p.GetType().GetField('apply',flags).GetValue(p).Enabled
with open(os.path.join(folder,'generation-state.json'),'w') as f:json.dump(dict(pid=EXPECTED_PID,jobId=job['id'],library=api('material_library')['directory'],reference=ref,targets=state['targets']),f,indent=2)
print(json.dumps(dict(started=True,jobId=job['id'],executor=job['executor'],stage=job['stage'],references=len(job['referenceImages']))))

import System,clr,json,os
from System.Reflection import BindingFlags
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import MaterialQuickController,McpApi
D=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'materials-v09');s=json.load(open(os.path.join(folder,'failure-state.json')));assert s['pid']==EXPECTED_PID
def api(op):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(D.RuntimeSerialNumber)))));assert r['ok'],r
 return r['result']
job=next(j for j in api('material_generation_jobs') if j['id']==s['jobId']);assert job['status']=='failed' and job['error'],job
state=api('material_quick_status');assert state['jobId'] is None and '失败' in state['status'],state
p=MaterialQuickController.Find(D.RuntimeSerialNumber);flags=BindingFlags.Instance|BindingFlags.NonPublic
assert p.GetType().GetField('generate',flags).GetValue(p).Enabled
# A retry may start immediately after failure; cancel it before any generation is needed.
p.GetType().GetMethod('Generate',flags).Invoke(p,None);retry=api('material_quick_status')['jobId'];assert retry
p.GetType().GetMethod('Cancel',flags).Invoke(p,None)
job2=next(j for j in api('material_generation_jobs') if j['id']==retry);assert job2['status']=='cancelled' and job2['material'] is None,job2
result=dict(passed=True,failureJob=s['jobId'],failureMessage=job['error'],retryJob=retry,retryCancelled=True)
with open(os.path.join(folder,'failure-verified.json'),'w') as f:json.dump(result,f,indent=2)
print(json.dumps(result))

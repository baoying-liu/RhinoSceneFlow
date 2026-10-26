import System,json,clr,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
D=__rhino_doc__;state=json.load(open(os.path.join(OUTPUT_DIR,'worlduv','quick-generation.json')))
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(D.RuntimeSerialNumber),**kw))));assert r['ok'],r
 return r['result']
p=api('material_quick_status');assert 'Reading reference image' in p['status'],p
jobs=api('material_generation_jobs');job=next(j for j in jobs if j['id']==state['jobId']);assert os.path.isfile(job['referenceImages'][0])
a=api('material_generation_complete',jobId=state['jobId'],files=dict(baseColor=job['referenceImages'][0]));state['newAsset']=a['id'];state['realStageDisplayed']=True
with open(os.path.join(OUTPUT_DIR,'worlduv','quick-generation.json'),'w') as f:json.dump(state,f,indent=2)
print(json.dumps(state))

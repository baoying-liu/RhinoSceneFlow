import Rhino,System,clr,json,os,hashlib
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
D=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'materials-v09');s=json.load(open(os.path.join(folder,'generation-state.json')));assert s['pid']==EXPECTED_PID
def api(op):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(D.RuntimeSerialNumber)))));assert r['ok'],r
 return r['result']
job=next(j for j in api('material_generation_jobs') if j['id']==s['jobId']);state=api('material_quick_status')
if job['status'] not in ['completed','failed','cancelled']:
 print(json.dumps(dict(pending=True,status=job['status'],stage=job['stage'],panelStatus=state['status'])))
else:
 assert job['status']=='completed',job
 assert state['jobId'] is None and state['selected']==job['material'],state
 asset=next(a for a in api('material_library')['assets'] if a['id']==job['material']);path=os.path.join(s['library'],'assets',asset['id'].replace('-',''),asset['maps']['baseColor'])
 assert os.path.isfile(path)
 digest=hashlib.sha256(open(path,'rb').read()).hexdigest();reference=hashlib.sha256(open(s['reference'],'rb').read()).hexdigest();assert digest!=reference,'Reference image was reused instead of generation'
 events=os.path.join(s['library'],'requests',job['id'].replace('-',''),'runner','events.jsonl')
 assert os.path.isfile(events)
 with open(events,encoding='utf-8') as f:lines=[json.loads(l) for l in f if l.strip()]
 thread=next(e['thread_id'] for e in lines if e['type']=='thread.started');assert any(e['type']=='turn.completed' for e in lines)
 result=dict(passed=True,pid=EXPECTED_PID,jobId=job['id'],assetId=asset['id'],assetPath=path,sha256=digest,referenceHash=reference,codexThread=thread,widthMeters=asset['widthMeters'],heightMeters=asset['heightMeters'],referencePassed=True,panelAutoSelected=True)
 with open(os.path.join(folder,'generation-verified.json'),'w') as f:json.dump(result,f,indent=2)
 print(json.dumps(result))

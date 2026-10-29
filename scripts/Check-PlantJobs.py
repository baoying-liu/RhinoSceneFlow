import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
folder=os.path.join(OUTPUT_DIR,'plants015');setup=json.load(open(os.path.join(folder,'final-start.json')))
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(__rhino_doc__.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
job=api('material_chat_status',jobId=setup['reuseJob']);report=dict(reuse=job)
if job['status']!='running':
 assert job['status']=='completed' and job['plantMatches'] and not job['plant'] and not job['imagePath'],job
 report['reusedWithoutNewImage']=True
 path=os.path.join(folder,'organize-start.json')
 if not os.path.isfile(path):
  before=api('plant_library')['assets'];org=api('plant_organize')
  with open(path,'w') as f:json.dump(dict(before=before,job=org['id']),f,indent=2)
 org=json.load(open(path));report['organize']=api('material_catalog_status',jobId=org['job'])
 if report['organize']['status']!='running':
  assert report['organize']['status']=='completed',report
  after=api('plant_library')['assets'];assert len(after)==len(org['before'])
  for old in org['before']:
   new=next(a for a in after if a['id']==old['id'])
   for key in ['plant','maps','sha256','widthMeters','heightMeters','revision']:assert old[key]==new[key],key
  report['organizePreservedIdentityImagesAndSize']=True
with open(os.path.join(folder,'jobs-status.json'),'w') as f:json.dump(report,f,indent=2)
print(json.dumps(report))

import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi,WorkbenchService
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.abspath(os.path.join(OUTPUT_DIR,'..','examples','Hillside-Retreat'));data=json.load(open(os.path.join(folder,'geometry.json')));queue=json.load(open(os.path.join(folder,'asset-queue.json')))
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
path=os.path.join(folder,'applied.json');applied=json.load(open(path)) if os.path.exists(path) else {}
randomPath=os.path.join(folder,'random-jobs.json');random=json.load(open(randomPath)) if os.path.exists(randomPath) else {}
for key,aid in queue['assets'].items():
 if key in applied:continue
 keys={'grass':['grass'],'cedar':['cedar'],'roof':['roof','plaster']}[key];ids=[oid for k in keys for oid in data['materialsets'][k]]
 asset=next(a for a in api('material_library')['assets'] if a['id']==aid)
 config=asset['randomization'];mode=config['recommendedMode'] if config['mode']=='auto' else config['mode']
 if mode!='off':
  if key not in random:
   random[key]=api('material_random_prepare',assetId=aid,objects=ids,preview=False)['id']
   with open(randomPath,'w') as f:json.dump(random,f,indent=2)
   print('Preparing AI-selected texture variation: '+key);continue
  job=api('material_random_status',jobId=random[key]);assert job['status'] not in ['failed','cancelled'],job
  if job['status']!='completed':print(json.dumps(job));continue
 result=api('material_apply',assetId=aid,objects=ids,mapping=dict(mode='plane' if key=='grass' else 'box'))
 applied[key]=dict(asset=aid,result=result,objects=ids)
with open(path,'w') as f:json.dump(applied,f,indent=2)
state=api('plant_group_state',groupId=json.load(open(os.path.join(folder,'planting.json')))['group'])
doc.Objects.UnselectAll();doc.NamedViews.Restore(0,doc.Views.ActiveView,False);doc.Views.Redraw()
b=WorkbenchService.Preview(doc,WorkbenchService.Settings(doc)[0],1200);b.Save(os.path.join(folder,'progress.png'),System.Drawing.Imaging.ImageFormat.Png);b.Dispose()
print(json.dumps(dict(applied=list(applied),plantCount=state['count'],manual=state['manual'],busy=state['busy'],error=state['error'])))

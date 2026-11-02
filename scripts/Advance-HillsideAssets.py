"""Advance one serial AI asset through the shipped SceneFlow API; never fabricates a result."""
import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.abspath(os.path.join(OUTPUT_DIR,'..','examples','Hillside-Retreat'))
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
path=os.path.join(folder,'asset-queue.json')
queue=json.load(open(path)) if os.path.exists(path) else dict(assets={},jobs={})
tree=api('material_chat_status',jobId=json.load(open(os.path.join(folder,'tree-job.json')))['id'])
assert tree['status']=='completed' and tree['plant'],tree
queue['tree']=tree['plant']
tasks=[
 ('grass',4,4,.92,'Hillside meadow / 草地','自然 / 草地',['草地','柔和','自然'], '生成一张无缝夏季草地base color材质，柔和鼠尾草绿和橄榄绿，短草与细小自然干草均匀交错，类似精致建筑景观模型中的草地。整张4米×4米。严格正交俯视、均匀中性漫射光，无阴影、高光、石头、花朵、土路、明显斑块和大色差，四边可重复。'),
 ('cedar',1.2,2.4,.72,'Weathered cedar / 风化雪松','木材 / 饰面',['木材','竖向','自然'], '生成无缝建筑外墙竖向雪松木板base color材质，温暖偏灰棕色，低饱和，自然细木纹，轻微风化。整张宽1.2米、高2.4米，宽度恰好8条150毫米竖直木板，细暗拼缝，木板沿图片竖向，板宽一致，无横缝。正面正交、均匀中性光，无阴影、高光、透视。'),
 ('roof',2,2,.78,'Ivory mineral finish / 米白矿物饰面','建筑 / 矿物',['浅色','细腻','哑光'], '生成无缝浅暖灰米白色细腻矿物建筑饰面base color，极细小均匀颗粒，非常克制的轻微色差，用于简化建筑屋面和上部外墙，2米×2米。整幅平整均匀，无接缝、砖块、污渍、裂缝、投影、高光和透视。')]
message=None
for key,w,h,rough,name,cat,tags,prompt in tasks:
 if key in queue['assets']:continue
 if key in queue['jobs']:
  state=next(j for j in api('material_generation_jobs') if j['id']==queue['jobs'][key]);queue.setdefault('states',{})[key]=state
  if state['status']=='completed':
   assert state['material'];queue['assets'][key]=state['material'];continue
  assert state['status'] not in ['failed','cancelled'],state
  message=dict(asset=key,status=state['status'],stage=state['stage']);break
 state=api('material_generation_start',asset=dict(name=name,category=cat,tags=tags,widthMeters=w,heightMeters=h,roughness=rough,source='ai-agent'),prompt=prompt)
 queue['jobs'][key]=state['id'];message=dict(asset=key,status=state['status'],stage=state['stage']);break
with open(path,'w') as f:json.dump(queue,f,indent=2)
print(json.dumps(message or dict(complete=True,assets=queue['assets'],tree=queue['tree'])))

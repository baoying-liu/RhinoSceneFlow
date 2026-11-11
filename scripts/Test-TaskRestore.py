"""Task restoration keeps AI settings and pending state honest; no model calls."""
import copy,json,sys,uuid
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/RhinoSceneFlow.Plugin/PostProduction'))
from board_store import Store
import canvas_context as context
out=ROOT/'artifacts/task-restore'/uuid.uuid4().hex;out.mkdir(parents=True);s=Store(out);b=s.create('Task restoration');bid=b['id'];p=out/'input.png';Image.new('RGB',(80,60),'#789075').save(p);a=s.put_asset(bid,p);root=s.append(bid,a,a,80,60,'source.png');n=s.branch(bid,root['id']);nid=n['id']
def board():return s.read(bid)
def node():return next(v for v in board()['nodes'] if v['id']==nid)
def ctl(action):return s.control(bid,nid,dict(revision=board()['revision'],action=action))
def mutate(fn):
 b=board();n=next(v for v in b['nodes'] if v['id']==nid);fn(b,n);s.commit(b,record=False)
mark=dict(id=uuid.uuid4().hex,kind='text',text='saved instruction',x=20,y=20,size=12,color='#123456',enabled=True,visible=True)
mutate(lambda b,n:n.update(annotations=[mark],guideControls=dict(enabled=True,specialEnabled=True)))
s.publish(bid,nid,a,a,80,60,'whole',{},dict(inputVersion=s.pixel_snapshot(root)))
before=copy.deepcopy(node());ctl('unlock')
mutate(lambda b,n:(n['guideControls'].update(enabled=False,specialEnabled=False,visible=False,specialVisible=False),n['annotations'][0].update(visible=False),n['params'].update(detail=90)))
assert node()['dirty'];ctl('cancel');restored=node()
assert restored['guideControls']==dict(enabled=True,specialEnabled=True,visible=False,specialVisible=False)
assert restored['annotations'][0]['visible'] is False
assert restored['params']==before['params'] and restored['locked'] and not restored['dirty']
assert restored['asset']==before['asset'] and restored['versionId']==before['versionId']
# Shared marks intentionally remain; restoration must not label this task clean.
ctl('unlock');pose=node()['pose'];world=dict(mark,id=uuid.uuid4().hex,x=pose['x']+30,y=pose['y']+30,text='shared canvas instruction')
mutate(lambda b,n:b['marks'].append(world));ctl('cancel');assert node()['dirty'] and len(board()['marks'])==1 and board()['marks'][0]['id']==world['id']
# Legacy saved tasks have no participation field: default gates restore safely.
ctl('unlock');mutate(lambda b,n:(n['baseline'].pop('participation',None),n['baseline']['params'].pop('editScope',None),b.update(marks=[]),n['guideControls'].update(enabled=False)))
ctl('cancel');assert node()['guideControls']['enabled'] and not node()['dirty']
restored=node();assert restored['params']['editScope']=='auto'
s.patch(bid,dict(revision=board()['revision'],view={**board()['view'],'mode':'canvas'},nodes=[{k:restored[k] for k in ('id','params','annotations')}]))
# Saved disabled groups, and backup checkout, must retain their own values.
ctl('unlock');mutate(lambda b,n:n['guideControls'].update(specialEnabled=False));s.publish(bid,nid,a,a,80,60,'whole',{},dict(inputVersion=s.pixel_snapshot(root)));ctl('unlock');mutate(lambda b,n:n['guideControls'].update(specialEnabled=True));ctl('cancel');assert not node()['guideControls']['specialEnabled'] and not node()['dirty']
v=node()['versions'][0];s.control(bid,nid,dict(revision=board()['revision'],action='checkout',version=v['versionId']));assert node()['guideControls']['specialEnabled'] and node()['dirty']
report=dict(groupParticipationRestored=True,visibilityRetained=True,sharedContextStillPending=True,legacyDefaults=True,backupParticipation=True,sourceUnchanged=True,modelCalls=0,folder=str(out));(out/'verified.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))


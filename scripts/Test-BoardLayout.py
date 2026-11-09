"""Frame/layout/history regression. No image or text model calls."""
import copy,json,random,sys,uuid
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/RhinoSceneFlow.Plugin/PostProduction'))
from board_store import Store
import board_layout as L
out=ROOT/'artifacts/layout022'/uuid.uuid4().hex;out.mkdir(parents=True);s=Store(out);b=s.create('Layout fixture');bid=b['id'];p=out/'pixel.png';Image.new('RGB',(100,75),'green').save(p);asset=s.put_asset(bid,p)
source=s.append(bid,asset,asset,100,75,'Source.psd');a=s.branch(bid,source['id']);b=s.branch(bid,source['id'])
def read():return s.read(bid)
def act(node,action,**kw):return s.control(bid,node,dict(revision=read()['revision'],action=action,**kw))
def history(direction):return s.history(bid,dict(revision=read()['revision'],direction=direction))
def cmd(action,**kw):return s.layout(bid,dict(revision=read()['revision'],action=action,**kw))
def no_overlap(board):
 nodes,_=L.visible(board['nodes'],board['view'].get('canvasCollapsed',[]))
 for i,n in enumerate(nodes):
  for m in nodes[i+1:]:assert not L.overlap(L.box(n),L.box(m)),(n['id'],m['id'])
no_overlap(read())
# One creation = one persistent undo command; redo restores same identity and pixel references.
last=b['id'];old=read();history('undo');assert last not in {n['id'] for n in read()['nodes']};history('redo');assert last in {n['id'] for n in read()['nodes']};no_overlap(read())
# Move into another frame: selected anchor stays at requested location; neighbors avoid it.
root=next(n for n in read()['nodes'] if n['id']==source['id']);moved=cmd('move',node=a['id'],x=root['pose']['x'],y=root['pose']['y']);no_overlap(moved)
assert next(n for n in moved['nodes'] if n['id']==a['id'])['pose']['x']==root['pose']['x']
# Oversized frame pushes neighbors without dirtying them; source identity/pixels preserved.
b=read();target=next(n for n in b['nodes'] if n['id']==a['id']);frame={**target['frame'],'width':2200,'height':1600}
s.patch(bid,dict(revision=b['revision'],nodes=[dict(id=a['id'],frame=frame)]));no_overlap(read());assert next(n for n in read()['nodes'] if n['id']==source['id'])['asset']==asset
history('undo');no_overlap(read());history('redo');no_overlap(read())
# Independent list collapse and per-child canvas collapse survive persistence and undo.
b=read();s.patch(bid,dict(revision=b['revision'],view={**b['view'],'collapsed':[source['id']]}))
cmd('toggle',node=a['id']);state=read();assert state['view']['collapsed']==[source['id']] and state['view']['canvasCollapsed']==[a['id']]
assert a['id'] not in [n['id'] for n in L.visible(state['nodes'],state['view']['canvasCollapsed'])[0]]
cmd('toggle',node=a['id']);no_overlap(read());assert read()['view']['collapsed']==[source['id']]
# Reversible deletion covers the branch, no physical asset deletion and no orphan reparenting.
act(source['id'],'delete');assert all(n['deleted'] for n in read()['nodes']);assert s.asset(bid,asset).exists()
# New Store instance: undo history is durable across service restart.
s=Store(out);history('undo');assert all(not n['deleted'] for n in read()['nodes']);history('redo');assert all(n['deleted'] for n in read()['nodes']);history('undo')
# Selection/camera are not undo commands, a fresh edit invalidates redo.
b=read();s.patch(bid,dict(revision=b['revision'],selectedId=a['id'],view={**b['view'],'camera':dict(x=123,y=456,scale=.6)}));history('undo');assert read()['view']['camera']['x']==123
n=next(n for n in read()['nodes'] if n['id']==a['id']);cmd('move',node=n['id'],x=n['pose']['x']+7,y=n['pose']['y']);assert read()['historyState']['redo']==0
# Deterministic stress cases and parity fixtures for the frontend.
rng=random.Random(22);nodes=[]
for i in range(80):
 n=copy.deepcopy(source);n.update(id=uuid.UUID(int=i+1).hex,parentId=nodes[(i-1)//3]['id'] if i else None);n['frame']=dict(x=-rng.randint(20,220),y=-rng.randint(20,170),width=rng.randint(450,1300),height=rng.randint(350,1000));n['pose']=dict(x=rng.randint(-500,1000),y=rng.randint(-500,1000),width=560,height=420);nodes.append(n)
arranged=L.arrange(nodes);no_overlap(dict(nodes=arranged,view={}))
anchor=arranged[3]['id'];trial=L.placements(arranged,{anchor:dict(x=arranged[0]['pose']['x'],y=arranged[0]['pose']['y'])});avoided=L.avoid(trial,anchor);no_overlap(dict(nodes=avoided,view={}))
fixture=dict(nodes=nodes,arranged=arranged,trial=trial,avoided=avoided,anchor=anchor)
(out/'parity.json').write_text(json.dumps(fixture));(ROOT/'artifacts/layout022-latest.json').write_text(json.dumps(dict(folder=str(out))))
report=dict(createUndoSingleStep=True,redoIdentity=True,persistentHistory=True,deleteSubtreeReversible=True,assetsRetained=True,frameCollisionAvoidance=True,moveAnchorPreserved=True,collapseIndependent=True,cameraExcludedFromUndo=True,newEditClearsRedo=True,stressNodes=80)
(out/'verified.json').write_text(json.dumps(report,indent=2));print(json.dumps(dict(folder=str(out),**report)))


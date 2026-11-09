"""Spatial inclusion, resource following, closed masks and parent-fill regression. Synthetic images only."""
import copy,json,sys,uuid
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/RhinoSceneFlow.Plugin/PostProduction'))
from board_store import Store
from board_api import BoardApi
from board_render import prepare
import canvas_context as ctx
out=ROOT/'artifacts/canvas-context'/uuid.uuid4().hex;out.mkdir(parents=True);store=Store(out);b=store.create('Spatial context');bid=b['id'];img=out/'input.png';Image.new('RGB',(80,60),'#8ea57f').save(img);asset=store.put_asset(bid,img);source=store.append(bid,asset,asset,80,60,'source.png');sid=source['id']
def board():return store.read(bid)
def node(id):return next(n for n in board()['nodes'] if n['id']==id)
def patch(**body):return store.patch(bid,dict(revision=board()['revision'],**body))
def mark(kind,x,y,text=''):
 return dict(id=uuid.uuid4().hex,kind=kind,x=x,y=y,text=text,points=[],size=18,color='#e8ae59',enabled=True)
p=node(sid)['pose'];outside=mark('label',p['x']-240,p['y']-30,'Use wood');inside=mark('text',p['x']+10,p['y']+10,'Preserve roof');patch(marks=[outside,inside]);api=BoardApi(out,{},None)
snap=api.snapshot(bid,sid);assert [a['id'] for a in snap['node']['annotations']]==[inside['id']]
ref=store.append(bid,asset,asset,80,60,'wood.png',kind='reference');rid=ref['id'];patch(nodes=[dict(id=rid,pose=dict(x=p['x']-220,y=p['y']+40,width=120,height=90))]);assert not api.snapshot(bid,sid)['references'];assert node(rid)['parentId'] is None
patch(nodes=[dict(id=sid,frame=dict(x=-280,y=-100,width=900,height=600))]);snap=api.snapshot(bid,sid);assert len(snap['references'])==1 and len(snap['node']['annotations'])==2;assert snap['references'][0]['relativePose']['x']==-220
# Captured items follow, while uncaptured items remain fixed in world coordinates.
far=mark('text',p['x']+1400,p['y'],'Outside');patch(marks=board()['marks']+[far]);prior=board();store.layout(bid,dict(revision=prior['revision'],action='move',node=sid,x=p['x']+130,y=p['y']+70));now=board();oldmarks={a['id']:a for a in prior['marks']};newmarks={a['id']:a for a in now['marks']};assert newmarks[inside['id']]['x']==oldmarks[inside['id']]['x']+130;assert newmarks[far['id']]==oldmarks[far['id']];assert node(rid)['pose']['x']==p['x']-220+130
# White draft can explicitly use pinned parent pixels, without publishing a fake generation.
draft=store.branch(bid,sid);did=draft['id'];before=board();store.control(bid,did,dict(revision=before['revision'],action='applyParent'));d=node(did);assert d['pending'] and d['draftBaseApplied'] and d['asset']==d['input']['asset'] and not d['locked'] and not d['versions']
store.history(bid,dict(revision=board()['revision'],direction='undo'));assert not node(did).get('draftBaseApplied');store.history(bid,dict(revision=board()['revision'],direction='redo'));assert node(did)['draftBaseApplied']
# Work on original source region: closed edit fills interior; protect wins inside it.
p=node(sid)['pose'];poly=lambda kind,pts:dict(id=uuid.uuid4().hex,kind=kind,points=[[p['x']+x,p['y']+y,.5] for x,y in pts],x=0,y=0,size=2,color='#e8ae59',closed=True,enabled=True)
edit=poly('edit',[(70,70),(490,70),(490,350),(70,350)]);protect=poly('protect',[(210,140),(350,140),(350,280),(210,280)]);arrow=poly('arrow',[(-160,80),(150,180)]);arrow.pop('closed');patch(marks=board()['marks']+[edit,protect,arrow]);snap=api.snapshot(bid,sid);snap['image']=str(store.asset(bid,node(sid)['asset']));folder=out/'raster';folder.mkdir();(folder/'snapshot.json').write_text(json.dumps(snap));prepare(folder)
mask=Image.open(folder/'mask.png');assert mask.getpixel((15,15))==255 and mask.getpixel((40,30))==0 and mask.getpixel((1,1))==0
prep=json.loads((folder/'prepared.json').read_text());assert prep['spatial']['references'][0]['number']==1;assert any(a.get('start') and a.get('end') for a in prep['spatial']['annotations']);assert any(a.get('text')=='Use wood' for a in prep['spatial']['annotations']);assert (folder/'reference-sheet.png').exists()
# Current geometry and detached resources survive package round trip.
restored=store.unpack(store.package(bid));assert restored['marks']==board()['marks'];assert any(n['kind']=='reference' and n['parentId'] is None for n in restored['nodes'])
report=dict(spatialFrameOnly=True,referenceNotSubject=True,frameExpandAbsorbs=True,resourcesFollowCapturedSubject=True,outsideStaysFixed=True,parentFillStillDraft=True,parentFillUndoRedo=True,closedPolygonInterior=True,protectWins=True,contextDiagramAndCoordinates=True,arrowReferenceRelationship=True,packagePreservesResources=True,modelCalls=0,folder=str(out));(out/'verified.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))


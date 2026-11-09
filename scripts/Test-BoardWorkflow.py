"""Workflow state/provenance regression. Synthetic pixels only; never invokes an image model."""
import asyncio,copy,json,sys,uuid
from pathlib import Path
from PIL import Image
from fastapi import HTTPException
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/RhinoSceneFlow.Plugin/PostProduction'))
from board_store import Store
from board_api import BoardApi
out=ROOT/'artifacts/workflow021'/uuid.uuid4().hex;out.mkdir(parents=True)
s=Store(out);b=s.create('Workflow regression');bid=b['id']
p=out/'source.png';Image.new('RGB',(80,60),'gray').save(p);a=s.put_asset(bid,p)
original=s.append(bid,a,a,80,60,'Input.psd',source={'psdAsset':None});oid=original['id']
def read(id):return next(n for n in s.read(bid)['nodes'] if n['id']==id)
def action(id,action,**extra):return s.control(bid,id,dict(revision=s.read(bid)['revision'],action=action,**extra))
def patch(id,**extra):return s.patch(bid,dict(revision=s.read(bid)['revision'],nodes=[dict(id=id,**extra)]))
def reject(fn):
 try:fn()
 except (ValueError,HTTPException):return
 raise AssertionError('Expected refusal')
def publish(id,color):
 n=read(id);parent,notes=s.effective(s.read(bid),n);snap={'inputVersion':s.pixel_snapshot(parent),'inputNotes':notes}
 if parent.get('original'):snap['inputTemplate']=dict(id=parent['id'],prompt=parent['params']['prompt'])
 Image.new('RGB',(80,60),color).save(p);asset=s.put_asset(bid,p)
 return s.publish(bid,id,asset,asset,80,60,'whole',{'syntheticFixture':True},snap)
assert not read(oid)['locked'];patch(oid,params={**original['params'],'prompt':'Template brief','detail':72});reject(lambda:s.publish(bid,oid,a,a,80,60,'whole',{},{}))
x=s.branch(bid,oid);xid=x['id'];assert read(xid)['pending'] and not read(xid)['locked'] and read(xid)['params']['prompt']=='Template brief' and read(xid)['params']['detail']==72 and read(oid)['params']['prompt']=='Template brief'
patch(xid,params={**x['params'],'prompt':'Wood cladding'});publish(xid,'red');assert read(xid)['locked'] and not read(xid)['pending'];assert read(oid)['params']['prompt']=='' and not read(oid)['locked']
reject(lambda:patch(xid,params={**read(xid)['params'],'prompt':'Blocked'}))
y=s.branch(bid,xid);yid=y['id'];assert y['params']['prompt']=='';assert y['input']['asset']==read(xid)['asset']
patch(yid,params={**y['params'],'prompt':'Refine roof'});publish(yid,'blue')
z=s.branch(bid,yid,True);assert z['parentId']==xid and z['input']['asset']==read(yid)['input']['asset']
# Layout only never marks clean image dirty; content draft and rollback survive reads.
patch(xid,pose={**read(xid)['pose'],'x':1600});assert not read(xid)['dirty']
action(xid,'unlock');patch(xid,params={**read(xid)['params'],'freedom':80});assert read(xid)['dirty'];action(xid,'cancel');assert read(xid)['params']['freedom']==15 and read(xid)['locked']
# Upstream updates mark only descendants whose actual direct inputs change.
action(xid,'unlock');publish(xid,'green');assert read(yid)['inputChanged'] and not read(yid)['dirty'];assert read(yid)['asset']!=read(xid)['asset']
old_input=read(yid)['input']['asset'];publish(yid,'yellow');assert not read(yid)['inputChanged'];assert read(yid)['input']['asset']!=old_input
# Archive is reversible; pixels do not revert.
asset_before=read(yid)['asset'];action(xid,'archive',summary='Retain timber cladding and refined openings.')
parent,notes=s.effective(s.read(bid),read(yid));assert parent['id']==oid and notes[0]['id']==xid and read(yid)['inputChanged']
action(xid,'restore');assert read(yid)['asset']==asset_before and not read(yid)['inputChanged']
# Two immutable backups, capacity before paid generation, +3 override and reset.
action(xid,'unlock');publish(xid,'purple');assert len(read(xid)['versions'])==2
backup=copy.deepcopy(read(xid)['versions'][0]);reject(lambda:s.check_capacity(read(xid)))
action(xid,'expand');assert read(xid)['backupLimit']==5
publish(xid,'orange');assert len(read(xid)['versions'])==3 and read(xid)['versions'][0]==backup
action(xid,'checkout',version=backup['versionId']);assert read(xid)['dirty'] and read(xid)['versions'][0]==backup
for v in list(read(xid)['versions'])[1:]:action(xid,'deleteBackup',version=v['versionId'])
assert read(xid)['backupLimit'] is None
action(xid,'autoPrune',enabled=True);publish(xid,'black');publish(xid,'white');assert len(read(xid)['versions'])==2
assert s.asset(bid,backup['asset']).exists() # retained provenance bytes, not garbage-collected
# Source naming, persistent IDs, archive package round trip.
assert read(oid)['name'].endswith('.psd');assert s.read(bid)==s.read(bid)
package=s.package(bid);restored=s.unpack(package);assert restored['nodes'][0]['id']==oid
async def queued_cancel():
 class Engine:
  image_gate=asyncio.Semaphore(0)
  async def image(self,*a):raise AssertionError('No model calls in fixture')
 jobs={}
 def new_job(id,kind):
  j=dict(id=uuid.uuid4().hex,status='queued');jobs[j['id']]=j;return j
 api=BoardApi(out,dict(codex=sys.executable,new_job=new_job),Engine())
 b=api.store.read(bid);task=await api.start(bid,z['id'],dict(revision=b['revision'],stage='whole'))
 jobs[task['job']]['status']='cancelled';future=api.active[task['job']];api.cancel(task['job'])
 try:await future
 except asyncio.CancelledError:pass
 await asyncio.sleep(0);api.tasks(bid);assert not read(z['id']).get('busy')
# Provide brief on pending sibling.
patch(z['id'],params={**read(z['id'])['params'],'prompt':'Sibling test'})
asyncio.run(queued_cancel())
report=dict(originalPixelsReadOnly=True,inputSettingsEditable=True,inputBriefConsumed=True,draftsNoModel=True,parentVersionPinned=True,siblingInput=True,rollback=True,layoutClean=True,stalePropagation=True,archiveReversible=True,capacityBeforeGeneration=True,immutableBackups=True,autoPrune=True,expandReset=True,packageRoundTrip=True,queuedCancel=True,modelCalls=0)
(out/'verified.json').write_text(json.dumps(report,indent=2));print(json.dumps(dict(folder=str(out),**report)))

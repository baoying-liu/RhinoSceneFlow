"""Shared resolver/preflight guards, zero model calls, independent synthetic board."""
import asyncio,copy,json,sys,uuid
from pathlib import Path
from PIL import Image
from fastapi import HTTPException
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/RhinoSceneFlow.Plugin/PostProduction'))
from board_api import BoardApi
from board_store import Store
from board_render import prepare,detail
out=ROOT/'artifacts/task-inputs'/uuid.uuid4().hex;out.mkdir(parents=True)
s=Store(out);b=s.create('Task input regression');bid=b['id'];p=out/'image.png';Image.new('RGBA',(96,72),'#678975').save(p);asset=s.put_asset(bid,p);source=s.append(bid,asset,asset,96,72,'source.png')
def read(id):return next(n for n in s.read(bid)['nodes'] if n['id']==id)
def patch(id,**kw):return s.patch(bid,dict(revision=s.read(bid)['revision'],nodes=[dict(id=id,**kw)]))
def control(id,action,**kw):return s.control(bid,id,dict(revision=s.read(bid)['revision'],action=action,**kw))
def rejected(fn):
 try:fn()
 except (ValueError,HTTPException):return
 raise AssertionError('Expected rejection')
def publish(id,color):
 n=read(id);parent,notes=s.effective(s.read(bid),n);Image.new('RGBA',(96,72),color).save(p);a=s.put_asset(bid,p)
 return s.publish(bid,id,a,a,96,72,'whole',dict(syntheticFixture=True),dict(inputVersion=s.pixel_snapshot(parent),inputNotes=notes))

revision=s.read(bid)['revision'];rejected(lambda:s.branch(bid,source['id'],stage='detail'));assert s.read(bid)['revision']==revision
c=s.branch(bid,source['id']);patch(c['id'],params={**c['params'],'prompt':'Cladding'});publish(c['id'],'#bcb08a')
hd=s.branch(bid,c['id'],stage='detail');assert hd['params']['generationStage']=='detail' and hd['params']['prompt']=='' and hd['input']['id']==c['id']
child=s.branch(bid,c['id'],stage='whole');patch(child['id'],params={**child['params'],'prompt':'Windows'})
api=BoardApi(out,dict(new_job=lambda *a:dict(id=uuid.uuid4().hex,status='queued')),None)
async def raster(job,operation,folder):{'prepare':prepare,'detail':detail}[operation](folder)
api.raster=raster
async def checks():
 before=copy.deepcopy(s.read(bid));plan=await api.preflight(bid,child['id'],dict(revision=before['revision'],stage='whole'))
 assert plan['input']['id']==c['id'] and plan['ready'] and plan['images'].keys()=={'input','context','mask'}
 assert s.read(bid)==before,'Input checking must not edit board/history/pixels'
 hp=await api.preflight(bid,hd['id'],dict(revision=before['revision'],stage='detail'));assert hp['ready'] and hp['references']==[] and hp['annotations']==[] and hp['images']=={}
 try:await api.preflight(bid,child['id'],dict(revision=before['revision']-1))
 except HTTPException as e:assert e.status_code==409
 else:raise AssertionError('Stale preflight must reject')
 # Re-rendering a completed node resolves its parent; continuing binds the result.
 assert api.generation_snapshot(bid,c['id'])['inputVersion']['id']==source['id']
 frozen=copy.deepcopy(read(child['id'])['input']);control(c['id'],'unlock');publish(c['id'],'#456879')
 snap=api.generation_snapshot(bid,child['id']);assert snap['inputVersion']['versionId']==read(c['id'])['versionId'] and frozen['versionId']!=snap['inputVersion']['versionId'];assert read(child['id'])['input']==frozen
 control(c['id'],'archive',summary='Retain intended cladding improvements')
 snap=api.generation_snapshot(bid,child['id']);assert snap['inputVersion']['id']==source['id'] and len(snap['inputNotes'])==1
 assert 'Retain intended cladding' in snap['node']['params']['prompt']
 # Editing during a raster check cannot produce an apparently current confirmation.
 async def changing(job,operation,folder):
  raster_result={'prepare':prepare,'detail':detail}[operation](folder)
  n=read(child['id']);patch(child['id'],params={**n['params'],'detail':66})
 api.raster=changing
 stale=await api.preflight(bid,child['id'],dict(revision=s.read(bid)['revision'],stage='whole'));assert stale['stale']
 report=dict(hdDraftAtomic=True,emptyHdBriefReady=True,preflightReadOnly=True,actualRasterInputs=True,latestParentMatchesExecution=True,pinnedComparisonPreserved=True,archiveResolution=True,stalePreflight=True,modelCalls=0,folder=str(out))
 (out/'verified.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
asyncio.run(checks())

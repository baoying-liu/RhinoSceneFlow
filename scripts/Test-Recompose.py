"""Synthetic transport/history guards. No model and no fake AI receipts."""
import sys,uuid,asyncio,time,copy,json
from pathlib import Path
from PIL import Image
from fastapi import HTTPException
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/RhinoSceneFlow.Plugin/PostProduction'))
from board_api import BoardApi
from project import write_json,read_json
out=ROOT/'artifacts/recompose0222'/uuid.uuid4().hex;out.mkdir(parents=True);jobs={}
def new_job(*a):
 j=dict(id=uuid.uuid4().hex,status='queued');jobs[j['id']]=j;return j
class FixtureGeneration:
 def __init__(self):self.calls=0;self.fail=False;self.value=dict(status='completed',tiles=[dict(status='completed')],output=dict(image='fixture-green.png',preview='fixture-green.png',width=40,height=30))
 def state(self,*a):return self.value
 def idle(self,*a):pass
 def folder(self,*a):return out
 async def resume(self,*a):
  self.calls+=1;j=new_job();j['status']='completed';self.value['status']='failed' if self.fail else 'completed';return dict(job=j['id'])
 def cancel(self,*a):pass
g=FixtureGeneration();api=BoardApi(out,dict(jobs=jobs,new_job=new_job),g);s=api.store;b=s.create('Recompose fixture');bid=b['id']
def asset(color,name):
 Image.new('RGBA',(40,30),color).save(out/name);return s.put_asset(bid,out/name)
rootasset=asset('#657a83','fixture-source.png');oldasset=asset('#496aad','fixture-old.png');newasset=asset('#52916c','fixture-green.png');root=s.append(bid,rootasset,rootasset,40,30,'input.png');whole=s.branch(bid,root['id']);whole=s.publish(bid,whole['id'],rootasset,rootasset,40,30,'whole',dict(syntheticFixture=True),dict(inputVersion=s.pixel_snapshot(root)))
hd=s.branch(bid,whole['id'],stage='detail');snapshot=api.generation_snapshot(bid,hd['id']);folder=api.task_folder(bid);task=dict(id=folder.name,board=bid,node=hd['id'],stage='detail',status='completed',project=uuid.uuid4().hex,run=uuid.uuid4().hex,created=time.time());write_json(folder/'task.json',task);write_json(folder/'snapshot.json',snapshot);s.publish(bid,hd['id'],oldasset,oldasset,40,30,'detail',dict(task=task['id'],syntheticFixture=True),snapshot)
def current():return next(n for n in s.read(bid)['nodes'] if n['id']==hd['id'])
async def call():return await api.recompose(bid,task['id'],dict(revision=s.read(bid)['revision']))
async def rejected():
 try:await call()
 except (ValueError,HTTPException):return
 raise AssertionError('Expected recompose guard')
async def tests():
 t=await call();await api.active[t['job']];n=current();assert n['asset']==newasset and n['versions'][0]['asset']==oldasset and n['input']['versionId']==whole['versionId'] and n['locked'];assert n['source']['recomposedFrom']==task['id']
 s.control(bid,n['id'],dict(revision=s.read(bid)['revision'],action='unlock'));s.patch(bid,dict(revision=s.read(bid)['revision'],nodes=[dict(id=n['id'],params={**n['params'],'freedom':89})]));await rejected();assert g.calls==1
 s.control(bid,n['id'],dict(revision=s.read(bid)['revision'],action='cancel'));s.preference(backupLimit=0);await rejected();assert g.calls==1;s.preference(backupLimit=2)
 g.fail=True;t=await call();await api.active[t['job']];assert read_json(s.folder(bid)/'tasks'/t['id']/'task.json')['status']=='failed';assert current()['asset']==newasset and len(current()['versions'])==1
 report=dict(immutableOldResultBackup=True,sameNodeAndInput=True,lockedAfterRebuild=True,changedSettingsRejected=True,capacityBeforeWork=True,failureDoesNotPublish=True,modelCalls=0,folder=str(out));write_json(out/'verified.json',report);print(json.dumps(report))
asyncio.run(tests())

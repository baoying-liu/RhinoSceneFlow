"""File/cancellation invariants with an explicitly blocked image gate; no model called."""
import asyncio,json,sys,tempfile,uuid
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/RhinoSceneFlow.Plugin/PostProduction'))
from board_api import BoardApi
from project import read_json

async def main():
 folder=ROOT/'artifacts/board-invariants'/uuid.uuid4().hex;folder.mkdir(parents=True)
 class BlockedEngine:
  image_gate=asyncio.Semaphore(0)
  async def image(self,*args):raise AssertionError('Model must never run in a cancellation fixture')
 jobs={}
 def new_job(id,kind):
  job=dict(id=uuid.uuid4().hex,project=id,kind=kind,status='queued');jobs[job['id']]=job;return job
 board=BoardApi(folder,dict(codex=sys.executable,new_job=new_job),BlockedEngine())
 b=board.store.create('Invariant fixture');p=folder/'source.png';Image.new('RGB',(80,60),'gray').save(p);asset=board.store.put_asset(b['id'],p)
 source=board.store.append(b['id'],asset,asset,80,60,'Source')
 n=board.store.branch(b['id'],source['id']);current=board.store.read(b['id']);board.store.patch(b['id'],dict(revision=current['revision'],nodes=[dict(id=n['id'],params={**n['params'],'prompt':'Fixture prompt'})]))
 for immediate in (True,False):
  b=board.store.read(b['id']);task=await board.start(b['id'],n['id'],dict(revision=b['revision'],stage='whole'))
  tf=board.store.folder(b['id'])/'tasks'/task['id'];snapshot=(tf/'snapshot.json').read_bytes()
  if not immediate:await asyncio.sleep(0)
  latest=board.store.read(b['id']);board.store.patch(b['id'],dict(revision=latest['revision'],nodes=[dict(id=n['id'],pose={**n['pose'],'x':500})]))
  assert snapshot==(tf/'snapshot.json').read_bytes()
  jobs[task['job']]['status']='cancelled';future=board.active[task['job']];board.cancel(task['job'])
  try:await future
  except asyncio.CancelledError:pass
  await asyncio.sleep(0)
  assert read_json(tf/'task.json')['status']=='cancelled'
  assert not (tf/'image-job').exists()
 report=dict(queuedCancel=True,waitingCancel=True,noModelCalls=True,snapshotImmutable=True)
 (folder/'verified.json').write_text(json.dumps(report));print(json.dumps(dict(folder=str(folder),**report)))
asyncio.run(main())

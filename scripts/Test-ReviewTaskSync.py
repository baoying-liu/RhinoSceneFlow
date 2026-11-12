"""Board review route -> generation -> board task synchronization. No model calls."""
import asyncio,copy,json,sys,time,uuid
from pathlib import Path
from PIL import Image
from fastapi import FastAPI,HTTPException

root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'src/RhinoSceneFlow.Plugin/PostProduction'))
from board_api import register
from project import read_json,write_json

async def test():
    out=root/'artifacts/review-task-sync'/uuid.uuid4().hex;out.mkdir(parents=True)
    jobs={}
    class Generation:
        def __init__(self):self.value=dict(status='partial',activeTile=None,stage='Review tile',output=None)
        def state(self,*args):return copy.deepcopy(self.value)
        def folder(self,*args):return out/'run'
        async def retry(self,project,run,tile):
            if self.value['status'] in ('queued','running'):raise HTTPException(409,'Already running')
            self.value.update(status='queued',activeTile=tile,stage='Queued',output=None)
            job=uuid.uuid4().hex;jobs[job]=dict(status='queued');return dict(job=job,run=run)
        async def accept(self,*args):return await self.retry(*args)
        async def resume(self,project,run):return await self.retry(project,run,2)
    class App:
        def include_router(self,router):self.routes=router.routes
    engine=Generation();app=App();board=register(app,out,dict(jobs=jobs),engine);store=board.store
    b=store.create('Review state fixture');bid=b['id'];p=out/'input.png';Image.new('RGB',(80,60),'gray').save(p)
    asset=store.put_asset(bid,p);n=store.append(bid,asset,asset,80,60,'Input.png');task=uuid.uuid4().hex
    folder=store.folder(bid)/'tasks'/task;folder.mkdir(parents=True)
    t=dict(id=task,board=bid,node=n['id'],job='old-parent-job',status='review',phase='review',created=time.time(),project=uuid.uuid4().hex,run=uuid.uuid4().hex,stage='detail')
    write_json(folder/'task.json',t);write_json(folder/'snapshot.json',dict(node=n))
    def mark_busy():
        b=store.read(bid);b['nodes'][0]['busy']=task;store.commit(b)
    mark_busy()
    route=next(r.endpoint for r in app.routes if getattr(r,'path','')=='/api/boards/{id}/tasks/{task}/review' and 'POST' in r.methods)
    child=await route(bid,task,dict(action='retry',tile=2))
    current=board.tasks(bid)[0]
    assert current['status']=='running' and current['phase']=='retrying' and current['activeTile']==2 and current['job']==child['job']
    assert store.read(bid)['nodes'][0]['busy']==task
    try:await route(bid,task,dict(action='retry',tile=2))
    except HTTPException as e:assert e.status_code==409
    else:raise AssertionError('Duplicate retry accepted')
    engine.value.update(status='running',activeTile=2,stage='Generating tile 2')
    current=board.tasks(bid)[0];assert current['status']=='running' and current['reviewStage']=='Generating tile 2'
    engine.value.update(status='partial',activeTile=None,stage='Tile still needs review')
    assert board.tasks(bid)[0]['status']=='review'
    # A cancelled retry releases the board busy state and stays cancelled on later polls.
    await route(bid,task,dict(action='retry',tile=2));engine.value.update(status='cancelled',activeTile=None)
    assert board.tasks(bid)[0]['status']=='cancelled' and 'busy' not in store.read(bid)['nodes'][0]
    assert board.tasks(bid)[0]['status']=='cancelled'
    # Completion publishes once, retains task ancestry, and clears the review binding.
    t.update(status='review',phase='review');write_json(folder/'task.json',t);engine.value['status']='partial';mark_busy()
    await route(bid,task,dict(action='retry',tile=2));run=out/'run';run.mkdir();Image.new('RGB',(80,60),'green').save(run/'result.png')
    engine.value.update(status='completed',activeTile=None,output=dict(image='result.png',preview='result.png',width=80,height=60))
    finished=board.tasks(bid)[0];assert finished['status']=='completed' and 'reviewJob' not in finished
    count=len(store.read(bid)['nodes']);assert count==2
    assert board.tasks(bid)[0]['result']==finished['result'] and len(store.read(bid)['nodes'])==count
    print(json.dumps(dict(retryMainTaskRunning=True,activeTile=2,duplicateBlocked=True,cancelReleasesBusy=True,publishedOnce=True,modelCalls=0,folder=str(out))))

asyncio.run(test())

"""Final-image admission and explicit approval guards. No model calls."""
import asyncio,sys,uuid,json
from pathlib import Path
from fastapi import HTTPException
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/RhinoSceneFlow.Plugin/PostProduction'))
from generation import Engine
from project import write_json,read_json
out=ROOT/'artifacts/final-review0223'/uuid.uuid4().hex;out.mkdir(parents=True);run=uuid.uuid4().hex;p=out/'runs'/run;p.mkdir(parents=True);updates=[]
def job(*a):return dict(id=uuid.uuid4().hex,status='queued')
engine=Engine(dict(project_dir=lambda id:out,update=lambda *a,**kw:updates.append(kw),new_job=job));state=dict(id=run,project=uuid.uuid4().hex,status='review',tiles=[dict(status='completed')],output=None);write_json(p/'run.json',state)
partial=True
async def raster(job,op,folder):write_json(folder/'composed.json',dict(accepted=1,partial=partial,needsReview=not partial,checks=dict(review=not partial,reasons=[] if partial else ['seam'],hardFailure=False),image='fixture.png'))
engine.raster=raster
async def main():
 global partial
 await engine.fuse(dict(status='running'),p,state);assert updates==[] and state['output']['partial'];partial=False
 await engine.fuse(dict(status='running'),p,state);assert updates==[] and state['output']['needsReview']
 try:await engine.accept_output(state['project'],run,uuid.uuid4().hex)
 except HTTPException as e:assert e.status_code==409
 else:raise AssertionError('Stale final result accepted')
 await engine.accept_output(state['project'],run,state['fusionId']);saved=read_json(p/'run.json');assert len(updates)==1 and saved['status']=='completed' and saved['output']['reviewAccepted']
 saved['output'].update(needsReview=True,checks=dict(hardFailure=True));write_json(p/'run.json',saved)
 try:await engine.accept_output(state['project'],run,state['fusionId'])
 except ValueError:pass
 else:raise AssertionError('Pixel corruption was allowed')
 report=dict(partialDoesNotReplaceLatest=True,reviewDoesNotReplaceLatest=True,staleApprovalRejected=True,explicitApprovalRequired=True,integrityFailureCannotBeApproved=True,modelCalls=0,folder=str(out));write_json(out/'verified.json',report);print(json.dumps(report))
asyncio.run(main())

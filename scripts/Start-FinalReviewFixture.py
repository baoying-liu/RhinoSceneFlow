"""Prepare an explicitly synthetic final-review state on the owned HTTP fixture."""
import sys,json,uuid,time,subprocess
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/RhinoSceneFlow.Plugin/PostProduction'))
from board_api import BoardApi
from project import write_json
subprocess.run([sys.executable,str(ROOT/'scripts/Start-BoardWorkflowFixture.py')],check=True)
r=json.loads((ROOT/'artifacts/workflow021-http-latest.json').read_text());out=Path(r['folder']);api=BoardApi(out,{},None);s=api.store;b=s.read(r['board']);whole=next(n for n in b['nodes'] if n['id']==r['child']);hd=s.branch(b['id'],whole['id'],stage='detail');snap=api.generation_snapshot(b['id'],hd['id']);s.publish(b['id'],hd['id'],whole['asset'],whole['preview'],160,120,'detail',dict(syntheticFixture=True),snap)
project=uuid.uuid4().hex;run=uuid.uuid4().hex;folder=out/'projects'/project;folder.mkdir(parents=True);p=folder/'runs'/run;p.mkdir(parents=True);Image.new('RGBA',(160,120),'#b8aa78').save(p/'synthetic-result.png');Image.new('RGB',(160,120),'#648b72').save(p/'synthetic-tile.png');write_json(folder/'project.json',dict(id=project,status='ready',name='Synthetic final-review fixture',latestRun=None))
write_json(p/'run.json',dict(id=run,project=project,status='review',created=time.time(),mode='all',fusionId=uuid.uuid4().hex,tiles=[dict(id=1,status='completed',image='synthetic-tile.png')],output=dict(image='synthetic-result.png',preview='synthetic-result.png',width=160,height=120,partial=False,accepted=1,needsReview=True,checks=dict(review=True,reasons=['seam'],hardFailure=False))))
task=s.folder(b['id'])/'tasks'/uuid.uuid4().hex;task.mkdir(parents=True);write_json(task/'snapshot.json',snap);write_json(task/'task.json',dict(id=task.name,job=uuid.uuid4().hex,board=b['id'],node=hd['id'],stage='detail',status='review',phase='review',created=time.time(),project=project,run=run));b=s.read(b['id']);b['selectedId']=hd['id'];next(n for n in b['nodes'] if n['id']==hd['id'])['busy']=task.name;s.commit(b);r.update(hd=hd['id'],task=task.name,oldAsset=whole['asset'],project=project,run=run);write_json(ROOT/'artifacts/final-review-http-latest.json',r)

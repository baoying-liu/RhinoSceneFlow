"""Isolated real-PSD Web fixture. Test token only; never uses user credentials."""
import json,os,subprocess,sys,time,urllib.request,uuid,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];payload=ROOT/'src/RhinoSceneFlow.Plugin/PostProduction';sys.path.insert(0,str(payload))
import project
from board_store import Store
out=ROOT/'artifacts/emission/browser'/uuid.uuid4().hex;out.mkdir(parents=True)
source=next((ROOT/'artifacts/rhino-B/emission0234/focused-object-glow').glob('*.psd'))
psdroot=out/'psd';psdroot.mkdir();shutil.copyfile(source,psdroot/'source.psd');project.prepare(psdroot)
document=project.read_json(psdroot/'document.json');store=Store(out);board=store.create('Emission channel validation');bid=board['id']
node=store.append(bid,store.put_asset(bid,psdroot/'composite.png'),store.put_asset(bid,psdroot/'preview.png'),document['width'],document['height'],'Emission.psd',source=dict(psdAsset=store.put_asset(bid,psdroot/'source.psd','.psd'),layers=document['layers']),stage='source')
store.preference(language='en',lastBoard=bid)
env=os.environ.copy();env['SCENEFLOW_POST_TOKEN']='emission-fixture-token'
proc=subprocess.Popen([sys.executable,'-I','-X','utf8',str(payload/'server.py'),'--data',str(out)],env=env,stdout=(out/'stdout.log').open('w'),stderr=(out/'stderr.log').open('w'),creationflags=subprocess.CREATE_NO_WINDOW)
for _ in range(150):
 if (out/'service.json').exists():
  svc=project.read_json(out/'service.json')
  try:
   with urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:'+str(svc['port'])+'/api/status',headers={'Authorization':'Bearer emission-fixture-token'}),timeout=1):break
  except OSError:pass
 assert proc.poll() is None,(out/'stderr.log').read_text();time.sleep(.1)
else:raise RuntimeError('Fixture startup failed')
record=dict(folder=str(out),board=bid,original=node['id'],pid=proc.pid,port=svc['port'])
(ROOT/'artifacts/emission/browser-fixture.json').write_text(json.dumps(record));print(json.dumps(record))

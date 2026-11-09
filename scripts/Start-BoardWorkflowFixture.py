"""Isolated HTTP service fixture; no model calls. Retained for component tests."""
import json,os,subprocess,sys,time,urllib.request,uuid
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];payload=ROOT/'src/RhinoSceneFlow.Plugin/PostProduction';sys.path.insert(0,str(payload))
from board_store import Store
out=ROOT/'artifacts/workflow021-http'/uuid.uuid4().hex;out.mkdir(parents=True)
s=Store(out);b=s.create('Workflow UI fixture');bid=b['id'];p=out/'fixture.png';Image.new('RGB',(160,120),'#9baf8d').save(p);a=s.put_asset(bid,p)
n=s.append(bid,a,a,160,120,'Architecture.psd');c=s.branch(bid,n['id']);b=s.read(bid)
s.patch(bid,dict(revision=b['revision'],nodes=[dict(id=c['id'],params={**c['params'],'prompt':'Refine cladding'})]))
Image.new('RGB',(160,120),'#648b72').save(p);a=s.put_asset(bid,p)
c=s.publish(bid,c['id'],a,a,160,120,'whole',dict(syntheticFixture=True),dict(inputVersion=s.pixel_snapshot(n)))
b=s.read(bid);b['selectedId']=n['id']
if '--edited-reference' in sys.argv:
 from psd_tools import PSDImage
 from psd_tools.api.layers import PixelLayer
 from PIL import ImageDraw
 for target in b['nodes']:
  im=Image.new('RGBA',(160,120),(0,0,0,0));ImageDraw.Draw(im).rectangle((40,30,119,89),fill='#ed4b44' if target['id']==c['id'] else '#416ac9')
  im.save(out/'reference.png');asset=s.put_asset(bid,out/'reference.png')
  psd=PSDImage.new('RGBA',im.size);psd.append(PixelLayer.frompil(im,psd,'Synthetic reference'));psd.save(out/'reference.psd')
  target['editReference']=dict(asset=asset,preview=asset,project=s.put_asset(bid,out/'reference.psd','.psd'),sourceAsset=target['asset'],width=160,height=120,enabled=True,updated=time.time())
 b['selectedId']=c['id']
s.commit(b)
s.preference(language='en',lastBoard=bid)
env=os.environ.copy();env['SCENEFLOW_POST_TOKEN']='workflow-fixture-token'
proc=subprocess.Popen([sys.executable,'-I','-X','utf8',str(payload/'server.py'),'--data',str(out)],env=env,stdout=(out/'stdout.log').open('w'),stderr=(out/'stderr.log').open('w'),creationflags=subprocess.CREATE_NO_WINDOW)
for _ in range(120):
 if (out/'service.json').exists():
  svc=json.loads((out/'service.json').read_text());base='http://127.0.0.1:'+str(svc['port'])
  try:
   with urllib.request.urlopen(urllib.request.Request(base+'/api/status',headers={'Authorization':'Bearer workflow-fixture-token'}),timeout=1):break
  except OSError:pass
 assert proc.poll() is None,(out/'stderr.log').read_text();time.sleep(.1)
else:raise RuntimeError('Fixture startup failed')
record=dict(folder=str(out),board=bid,original=n['id'],child=c['id'],pid=proc.pid,port=svc['port'])
(ROOT/'artifacts/workflow021-http-latest.json').write_text(json.dumps(record));print(json.dumps(record))

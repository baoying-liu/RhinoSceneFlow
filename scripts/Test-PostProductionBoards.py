"""Real local HTTP/files/worker tests. Optional --images uses ONE real Codex image call."""
import argparse,hashlib,json,os,subprocess,sys,time,urllib.request,urllib.error,uuid,zipfile
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--keep',action='store_true');parser.add_argument('--images',action='store_true');args=parser.parse_args()
out=ROOT/'artifacts/boards020'/uuid.uuid4().hex;out.mkdir(parents=True)
payload=ROOT/'src/RhinoSceneFlow.Plugin/PostProduction';codex=str(Path(os.environ['LOCALAPPDATA'])/'Programs/OpenAI/Codex/bin/codex.exe')
command=[sys.executable,'-I','-X','utf8',str(payload/'server.py'),'--data',str(out),'--codex',codex]
env=os.environ.copy();env['SCENEFLOW_POST_TOKEN']='board-fixture-ui-token'
process=subprocess.Popen(command,env=env,stdout=(out/'stdout.log').open('w'),stderr=(out/'stderr.log').open('w'),creationflags=subprocess.CREATE_NO_WINDOW)
base=None
def api(path,body=None,method=None):
 data=json.dumps(body).encode() if body is not None else None
 r=urllib.request.Request(base+'/api'+path,data=data,headers={'Authorization':'Bearer board-fixture-ui-token','Content-Type':'application/json'},method=method)
 with urllib.request.urlopen(r,timeout=180) as response:return json.load(response)
def blob(path):
 with urllib.request.urlopen(urllib.request.Request(base+'/api'+path,headers={'Authorization':'Bearer board-fixture-ui-token'}),timeout=180) as r:return r.read()
def rejected(code,path,body=None,method=None):
 try:api(path,body,method)
 except urllib.error.HTTPError as e:assert e.code==code,(e.code,e.read());return
 raise AssertionError('Expected HTTP '+str(code))
def worker(op,folder):subprocess.run([sys.executable,'-I','-X','utf8',str(payload/'board_render.py'),op,str(folder)],check=True,capture_output=True)
try:
 for _ in range(150):
  if (out/'service.json').exists():
   service=json.loads((out/'service.json').read_text());base='http://127.0.0.1:'+str(service['port'])
   try:api('/status');break
   except OSError:pass
  assert process.poll() is None,(out/'stderr.log').read_text();time.sleep(.1)
 else:raise AssertionError('Service not ready')
 b=api('/boards',{'name':'Interaction test · synthetic rough model'});bid=b['id']
 image=Image.new('RGBA',(640,480),'white');d=ImageDraw.Draw(image)
 d.polygon([(70,350),(410,440),(595,290),(260,225)],fill='#8a9b67');d.polygon([(180,300),(340,345),(340,205),(180,165)],fill='#b5a38c');d.polygon([(340,345),(460,265),(460,128),(340,205)],fill='#859290');d.polygon([(180,165),(300,95),(460,128),(340,205)],fill='#d4d4ce');d.rectangle((210,220,260,275),fill='#466572');d.rectangle((292,242,320,335),fill='#4b5358')
 image.save(out/'rough-house.png')
 imported=api('/boards/'+bid+'/import-path',{'path':str(out/'rough-house.png')})['node'];nid=imported['id'];b=api('/boards/'+bid)
 assert len(b['nodes'])==1 and b['nodes'][0]['width']==640
 sourceid=nid;imported=api('/boards/'+bid+'/nodes/'+nid+'/branch',{'revision':b['revision']});nid=imported['id'];b=api('/boards/'+bid)
 patch=dict(id=nid,pose={**imported['pose'],'x':950,'y':-250},params={**imported['params'],'prompt':'Complete this simple architectural massing as a refined daylight architectural visualization. Add clearly visible timber siding, window frames and crisp roof edges while retaining the camera and major building shape.'})
 b=api('/boards/'+bid,{'revision':b['revision'],'nodes':[patch]},'PUT');assert next(n for n in b['nodes'] if n['id']==nid)['name']==imported['name'] and next(n for n in b['nodes'] if n['id']==nid)['asset']==imported['asset']
 rejected(409,'/boards/'+bid,{'revision':0,'nodes':[]},'PUT')
 rejected(400,'/boards/'+bid,{'revision':b['revision'],'nodes':[{'id':nid,'params':{**patch['params'],'tileSize':512,'overlap':256}}]},'PUT')
 ref=api('/boards/'+bid+'/import-path',{'path':str(out/'rough-house.png'),'kind':'reference','owner':nid})['node'];b=api('/boards/'+bid)
 owner=next(n for n in b['nodes'] if n['id']==nid)
 notes=[dict(id=uuid.uuid4().hex,kind='protect',points=[[20,90,.5],[460,90,.8]],size=30,color='#ee5555',enabled=True),dict(id=uuid.uuid4().hex,kind='text',x=140,y=190,points=[],text='Refine window frame and wood siding',size=20,color='#e6aa55',enabled=True)]
 b=api('/boards/'+bid,{'revision':b['revision'],'nodes':[dict(id=nid,annotations=notes)]},'PUT')
 # Worker snapshot uses immutable source assets. Synthetic candidate is explicitly a pixel oracle.
 test=out/'raster-oracle';test.mkdir();node=next(n for n in b['nodes'] if n['id']==nid)
 snap=dict(node=node,image=str(out/'boards'/bid/'assets'/node['asset']),references=[dict(path=str(out/'rough-house.png'),clip=[0,0,1,1],relativePose=dict(x=500,y=50,width=100,height=100),node=dict(id=uuid.uuid4().hex,params=dict(referencePurpose='material'))) for _ in range(4)])
 (test/'snapshot.json').write_text(json.dumps(snap));worker('prepare',test)
 with Image.open(test/'reference-sheet.png') as sheet:assert sheet.size==(1536,1536)
 Image.new('RGB',(640,480),(235,100,55)).save(test/'generated.png');worker('finish',test)
 a=np.asarray(Image.open(test/'base.png'));r=np.asarray(Image.open(test/'result.png'));m=np.asarray(Image.open(test/'mask.png'))
 assert np.any(m==0) and np.any(m>0) and np.array_equal(a[m==0],r[m==0]) and np.array_equal(a[:,:,3],r[:,:,3])
 assert np.count_nonzero(np.any(a[:,:,:3]!=r[:,:,:3],axis=2))>10000
 # Native PSD import keeps embedded source and per-layer pixel protection portable.
 from psd_tools import PSDImage
 from psd_tools.api.layers import PixelLayer
 psd=PSDImage.new('RGBA',(80,60));psd.append(PixelLayer.frompil(Image.new('RGBA',(80,60),(90,110,130,255)),psd,'Editable'))
 top=Image.new('RGBA',(80,60));ImageDraw.Draw(top).rectangle((10,10,50,40),fill=(200,40,30,128));psd.append(PixelLayer.frompil(top,psd,'Locked'))
 psd.save(out/'layered.psd');psdnode=api('/boards/'+bid+'/import-path',{'path':str(out/'layered.psd')})['node'];b=api('/boards/'+bid)
 test_psd=out/'psd-oracle';test_psd.mkdir();psdnode['params']['roles']={'2':'preserve'};psdnode['params']['edgeGuard']=0
 psdroot=out/'boards'/bid/'assets';psnap=dict(node=psdnode,image=str(psdroot/psdnode['asset']),psd=str(psdroot/psdnode['source']['psdAsset']),layers=psdnode['source']['layers'],references=[])
 (test_psd/'snapshot.json').write_text(json.dumps(psnap));worker('prepare',test_psd)
 pm=np.asarray(Image.open(test_psd/'mask.png'));assert pm[20,20]==0 and pm[55,70]>0
 psdnode['params']['roles']={'2':'structure'};(test_psd/'snapshot.json').write_text(json.dumps(psnap));worker('prepare',test_psd)
 assert np.asarray(Image.open(test_psd/'mask.png'))[20,20]>0
 for fmt in ('png','jpg','webp'):
  data=blob('/boards/'+bid+'/nodes/'+sourceid+'/export?format='+fmt);p=out/('export.'+fmt);p.write_bytes(data)
  with Image.open(p) as im:assert im.size==(640,480)
 json_export=api('/boards/'+bid+'/export',dict(node=sourceid,format='webp',blend=100));assert Path(json_export['path']).is_file()
 json_package=api('/boards/'+bid+'/save',{});assert Path(json_package['path']).suffix=='.sflowboard'
 with zipfile.ZipFile(json_package['path']) as z:assert 'board.json' in z.namelist()
 package=out/'test.sflowboard';package.write_bytes(blob('/boards/'+bid+'/download'))
 reopened=api('/boards/'+bid+'/import-path',{'path':str(package)})['board'];copy=api('/boards/'+reopened)
 assert copy['id']!=bid and copy['nodes']==b['nodes'] and copy['view']==b['view']
 malicious=out/'malicious.sflowboard'
 with zipfile.ZipFile(malicious,'w') as z:z.writestr('../outside.txt','no');z.writestr('board.json','{}')
 rejected(400,'/boards/'+bid+'/import-path',{'path':str(malicious)})
 clone=api('/boards/'+bid+'/duplicate',{'name':'Independent copy'});assert clone['nodes']==b['nodes']
 prefs=api('/board-preferences',{'language':'en','lastBoard':bid},'PUT');assert prefs['language']=='en'
 rejected(400,'/board-preferences',{'language':'invalid'},'PUT')
 # Immutable identity fields supplied by a client cannot replace the actual pixels.
 b=api('/boards/'+bid,{'revision':b['revision'],'nodes':[{'id':nid,'asset':'../../outside.png','width':1}]},'PUT');assert next(n for n in b['nodes'] if n['id']==nid)['asset']==node['asset'] and next(n for n in b['nodes'] if n['id']==nid)['width']==640
 actual=None
 if args.images:
  task=api('/boards/'+bid+'/generate',{'node':nid,'revision':b['revision'],'stage':'whole'})
  for _ in range(1800):
   job=api('/jobs/'+task['job'])
   if job['status'] not in ('queued','running'):break
   time.sleep(1)
  assert job['status']=='completed',job
  current=api('/boards/'+bid);result=next(n for n in current['nodes'] if n['id']==job['result']['node'])
  assert result['id']==nid and result['parentId']==sourceid and result['stage']=='whole' and result['source']['receipt']['newImage']
  assert result['source']['report']['changedPixels']>0
  actual=dict(result=result['id'],receipt=result['source']['receipt'],report=result['source']['report'])
 report=dict(board=bid,node=nid,base=base,sourceHash=hashlib.sha256((out/'rough-house.png').read_bytes()).hexdigest(),revisionGuard=True,layoutIndependent=True,invalidOverlapRejected=True,portablePackage=True,zipTraversalRejected=True,formats=True,languagePersisted=True,exactProtectedPixels=True,exactAlpha=True,immutableAsset=True,layeredPsd=True,structureRoleEditable=True,fourReferencesOneSheet=True,realImage=actual)
 (out/'verified.json').write_text(json.dumps(report,indent=2));print(json.dumps(dict(evidence=str(out),board=bid,node=nid,base=base,realImage=bool(actual))))
 if args.keep:
  (ROOT/'artifacts/boards020-latest.json').write_text(json.dumps(dict(folder=str(out),board=bid,node=nid,port=service['port'],pid=process.pid)))
finally:
 if not args.keep:
  if base:
   try:api('/shutdown',{});process.wait(10)
   except Exception:process.terminate()
  elif process.poll() is None:process.terminate()

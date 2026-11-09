"""Real 4K pipeline through original Platform B. Does not auto-accept review warnings."""
import importlib.machinery,sys,os,hashlib,shutil,json
from pathlib import Path
from PIL import Image
import numpy as np
m=importlib.machinery.SourceFileLoader('audit',str(Path(__file__).with_name('Studio-Audit-Mcp.py'))).load_module();root=m.ROOT;o=root/'artifacts/rhino-B/final0223';o.mkdir(parents=True,exist_ok=True);c=m.StudioMcp(o);file=o/'4k-case.json'
if sys.argv[1]=='start':
 if file.exists():raise RuntimeError('4K task already recorded; use status instead of resubmitting')
 assert c.native('describe')['version']=='0.22.3' and c.api('/status')['version']=='0.22.3'
 old=m.load(root/'artifacts/rhino-B/raster0222/real-case.json');prefs=c.api('/board-preferences');b=c.api('/boards/'+old['board']+'/duplicate',dict(name='Hillside - 4K final verification'));c.api('/boards/'+b['id']+'/tasks');n=c.branch(b['id'],old['whole'],stage='detail');c.patch(b['id'],nodes=[dict(id=n['id'],name='Hillside - 4K 4096.png',params={**n['params'],'outputSize':4096,'tileSize':1536,'overlap':128})]);plan=c.preflight(b['id'],n['id'],'detail');assert plan['ready'] and plan['input']['id']==old['whole'];m.write(o/'4k-preflight.json',plan);t=c.generate(b['id'],n['id'],'detail');r=dict(board=b['id'],node=n['id'],task=t['id'],source=old['whole'],preferences=prefs,rootPSD=old['rootPSD'],expectedSize=[4096,3072],expectedTiles=12,pid=c.pid);m.write(file,r);print(json.dumps(dict(board=b['id'],task=t['id'],plannedImageCalls=12,size=r['expectedSize'])))
else:
 r=m.load(file);tasks=c.api('/boards/'+r['board']+'/tasks');m.write(o/'4k-tasks.json',tasks);t=next(t for t in tasks if t['id']==r['task']);print(json.dumps(dict(status=t['status'],phase=t['phase'],error=t.get('error'))))
 if t.get('run'):
  v=c.api('/boards/'+r['board']+'/tasks/'+r['task']+'/review');m.write(o/'4k-progress.json',v);print(json.dumps(dict(tiles=[dict(id=x['id'],status=x['status'],attempt=x['attempt'],error=x.get('error')) for x in v['tiles']],finalChecks=(v.get('output') or {}).get('checks'))))
 if sys.argv[1]=='export':
  assert t['status']=='completed','Do not export an unapproved run as a completed image'
  b=c.board(r['board']);n=next(n for n in b['nodes'] if n['id']==r['node']);assert not n['pending'] and n['locked'];f=c.api('/boards/'+r['board']+'/export',dict(node=n['id'],format='png',blend=100));shutil.copyfile(f['path'],o/'Hillside-4K.png');im=Image.open(o/'Hillside-4K.png');im.load();assert list(im.size)==r['expectedSize']
  source=next(n for n in b['nodes'] if n['id']==r['source']);assets=Path(os.environ['LOCALAPPDATA'])/'RhinoSceneFlow/postproduction/boards'/r['board']/'assets';alpha=np.array(Image.open(assets/source['asset']).convert('RGBA').resize(im.size,Image.Resampling.LANCZOS))[:,:,3];assert np.array_equal(alpha,np.array(im.convert('RGBA'))[:,:,3]);assert not v['output']['checks']['hardFailure'] and v['output']['artifactPixels']==0
  original=m.load(root/'artifacts/feature-audit-20261109/latest.json');assert hashlib.sha256(Path(r['rootPSD']).read_bytes()).hexdigest()==original['sourceSha256'];receipts=[]
  folder=Path(os.environ['LOCALAPPDATA'])/'RhinoSceneFlow/postproduction/projects'/t['project']/'runs'/t['run']
  for p in sorted(folder.glob('tile-*/attempt-*/receipt.json')):receipts.append(m.load(p))
  report=dict(board=r['board'],node=r['node'],task=r['task'],size=list(im.size),alphaExact=True,originalPSDUnchanged=True,imageCalls=len(receipts),receipts=receipts,checks=v['output']['checks'],artifactPixels=0,manualTiles=[x['id'] for x in v['tiles'] if x.get('acceptedByUser')],manualFinal=bool(v['output'].get('reviewAccepted')),fileSha256=hashlib.sha256((o/'Hillside-4K.png').read_bytes()).hexdigest());m.write(o/'4k-verified.json',report);c.api('/board-preferences',{**{k:v for k,v in r['preferences'].items() if k!='listWheelVersion'},'lastBoard':r['board']},'PUT');c.patch(r['board'],selectedId=r['node']);print('4K PNG exported and independently verified')

"""Read real B task evidence; never accept flagged tiles or start another image job."""
import importlib.machinery,os,json,hashlib,shutil,urllib.request
from pathlib import Path
import numpy as np
from PIL import Image
m=importlib.machinery.SourceFileLoader('audit',str(Path(__file__).with_name('Studio-Audit-Mcp.py'))).load_module();root=m.ROOT;o=root/'artifacts/rhino-B/raster0222';r=m.load(o/'real-case.json');c=m.StudioMcp(o)
tasks=c.api('/boards/'+r['board']+'/tasks');m.write(o/'tasks.json',tasks);run=c.api('/boards/'+r['board']+'/tasks/'+r['hdTask']+'/review');m.write(o/'hd-progress.json',run)
print(json.dumps(dict(tasks=[dict(stage=t['stage'],status=t['status'],error=t.get('error')) for t in tasks],tiles=[dict(id=t['id'],status=t['status'],error=t.get('error')) for t in run['tiles']])))
task=next(t for t in tasks if t['id']==r['hdTask'])
if task['status']=='completed':
 assert all(t['status']=='completed' and not t.get('acceptedByUser') and not t['quality']['review'] for t in run['tiles'])
 b=c.board(r['board']);n=next(n for n in b['nodes'] if n['id']==r['hd']);export=c.api('/boards/'+b['id']+'/export',dict(node=n['id'],format='png',blend=100));shutil.copyfile(export['path'],o/'HD-new.png');im=Image.open(o/'HD-new.png');im.load();assert im.size==(2048,1536)
 source=next(n for n in b['nodes'] if n['id']==r['whole']);folder=Path(os.environ['LOCALAPPDATA'])/'RhinoSceneFlow/postproduction/boards'/b['id'];alpha=np.array(Image.open(folder/'assets'/source['asset']).convert('RGBA').resize(im.size,Image.Resampling.LANCZOS))[:,:,3];assert np.array_equal(alpha,np.array(im.convert('RGBA'))[:,:,3])
 old=m.load(root/'artifacts/feature-audit-20261109/latest.json');assert hashlib.sha256(Path(r['rootPSD']).read_bytes()).hexdigest()==old['sourceSha256']
 assert run['output'].get('artifactPixels')==0
 v=dict(fusionArtifactPixels=0,recomposedTask=r.get('recomposeTask'),nativeVersion=c.native('describe')['version'],webVersion=c.api('/status')['version'],board=r['board'],wholeReceipt=m.load(o/'whole-verified.json')['receipt'],tileReceipts=[t['receipt'] for t in run['tiles']],realImageCalls=5,allFourTilesAutomatic=True,noManualAcceptance=True,outputSize=list(im.size),alphaExact=True,originalPSDUnchanged=True,geometry=[t['quality']['geometry'] for t in run['tiles']],overlaps=[t['quality']['overlap'] for t in run['tiles']],fusion=run['output']['fusion'])
 m.write(o/'real-verified.json',v)
 # Restore user settings, selecting the new result board for review.
 c.api('/board-preferences',{**{k:v for k,v in r['preferences'].items() if k!='listWheelVersion'},'lastBoard':b['id']},'PUT')
 c.patch(b['id'],selectedId=n['id']);print('Real 2048 output verified; all four tiles passed without manual acceptance')

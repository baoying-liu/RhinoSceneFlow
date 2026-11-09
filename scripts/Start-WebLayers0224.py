"""Update the independently owned Web worker without starting/restarting Rhino.

Native B 0.22.4 is already installed. The last change is a Web bundle only.
Keep immutable sandbox deployment files intact; native ExistingAsync adopts the
authenticated service via the existing service.json contract.
"""
import json,os,sys,shutil,subprocess,time,urllib.request,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'artifacts/rhino-B/layers0224';data=Path(os.environ['LOCALAPPDATA'])/'RhinoSceneFlow/postproduction';old=json.loads((data/'service.json').read_text(encoding='utf-8-sig'))
if old['version']!='0.22.4':raise RuntimeError('Expected installed 0.22.4 service')
headers={'Authorization':'Bearer '+old['token']};url='http://127.0.0.1:'+str(old['port'])+'/api/status'
try:
 with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=1):raise RuntimeError('Service already running; do not replace it blindly')
except OSError:pass
snapshot=out/'web-runtime'
if snapshot.exists():raise RuntimeError('Web snapshot already exists; inspect its record before retrying')
source=ROOT/'src/RhinoSceneFlow.Plugin/PostProduction';shutil.copytree(source,snapshot,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
# Update the owned distributable/build cache, not immutable sandbox deployment files.
for destination in [ROOT/'artifacts/package/RhinoSceneFlow/PostProduction',ROOT/'src/RhinoSceneFlow.Plugin/bin/Release/net8.0-windows/PostProduction']:
 for file in source.iterdir():
  if file.is_file() and file.suffix in ('.py','.js','.css','.html','.txt'):shutil.copyfile(file,destination/file.name)
env=os.environ.copy();env['SCENEFLOW_POST_TOKEN']=old['token']
p=subprocess.Popen([sys.executable,'-I','-X','utf8',str(snapshot/'server.py'),'--data',str(data),'--port',str(old['port'])],env=env,stdout=(out/'web-stdout.log').open('w'),stderr=(out/'web-stderr.log').open('w'),creationflags=subprocess.CREATE_NO_WINDOW)
for _ in range(100):
 if p.poll() is not None:raise RuntimeError('Web worker exited; see owned stderr log')
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=1) as r:s=json.load(r)
  if s['version']=='0.22.4':break
 except OSError:pass
 time.sleep(.1)
else:raise RuntimeError('Web startup not confirmed; keep PID '+str(p.pid))
record=dict(pid=p.pid,version=s['version'],runtime=str(snapshot),nativeRestarted=False,nativeVersion='0.22.4',bundleSha256=hashlib.sha256((snapshot/'board.js').read_bytes()).hexdigest(),sourceBundleMatches=hashlib.sha256((snapshot/'board.js').read_bytes()).digest()==hashlib.sha256((source/'board.js').read_bytes()).digest(),reason='Sandbox restart admission denied above 94% system commit; only the independent Web worker needed a final bundle refresh.')
(out/'web-runtime-verified.json').write_text(json.dumps(record,indent=2));print(json.dumps(record))

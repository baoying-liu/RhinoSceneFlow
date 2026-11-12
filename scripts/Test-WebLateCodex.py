"""Real isolated HTTP service: discover Codex installed after launch; no executable/model calls."""
import json,os,subprocess,sys,time,urllib.request,uuid
from pathlib import Path
root=Path(__file__).resolve().parents[1]
out=root/'artifacts/readiness-0231'/uuid.uuid4().hex;out.mkdir(parents=True)
home=out/'home';home.mkdir()
fake=home/'late-codex.exe'
env=dict(os.environ,SCENEFLOW_POST_TOKEN='readiness-fixture-token',USERPROFILE=str(home),HOME=str(home),PATH='',RHINOSCENEFLOW_CODEX=str(fake))
server=subprocess.Popen([sys.executable,'-I','-X','utf8',str(root/'src/RhinoSceneFlow.Plugin/PostProduction/server.py'),'--data',str(out/'service')],env=env,stdout=subprocess.DEVNULL,stderr=(out/'server.log').open('w',encoding='utf8'))
try:
    config=out/'service/server.json'
    # Server discovery file uses the existing service.json contract.
    config=out/'service/service.json'
    deadline=time.monotonic()+25
    while not config.exists():
        if server.poll() is not None:raise RuntimeError('Fixture service exited; see '+str(out/'server.log'))
        if time.monotonic()>deadline:raise TimeoutError('Fixture service did not start')
        time.sleep(.1)
    settings=json.loads(config.read_text());base='http://127.0.0.1:'+str(settings['port'])
    def call(route,post=False):
        req=urllib.request.Request(base+route,data=b'{}' if post else None,headers={'Authorization':'Bearer readiness-fixture-token','Content-Type':'application/json'})
        return json.load(urllib.request.urlopen(req,timeout=10))
    assert not call('/api/status')['codexAvailable']
    fake.write_bytes(b'not an executable; must never run')
    assert call('/api/status')['codexAvailable']
    fake.unlink()
    assert not call('/api/status')['codexAvailable']
    call('/api/shutdown',True);server.wait(timeout=10)
    print(json.dumps(dict(realHttp=True,lateInstallDetected=True,removedExecutableDetected=True,modelCalls=0,folder=str(out))))
finally:
    if server.poll() is None:server.terminate();server.wait(timeout=10)

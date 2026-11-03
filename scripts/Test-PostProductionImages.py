"""Real app-owned image smoke test. --images explicitly consumes image quota; no mock provider."""
import argparse,json,os,subprocess,sys,time,urllib.request,urllib.error,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--psd',required=True);parser.add_argument('--codex',required=True)
parser.add_argument('--images',action='store_true');parser.add_argument('--keep',action='store_true');args=parser.parse_args()
folder=ROOT/'artifacts/postproduction-images'/uuid.uuid4().hex;folder.mkdir(parents=True)
command=[sys.executable,'-I','-X','utf8',str(ROOT/'src/RhinoSceneFlow.Plugin/PostProduction/server.py'),'--data',str(folder),'--codex',args.codex]
process=subprocess.Popen(command,stdout=(folder/'stdout.log').open('w'),stderr=(folder/'stderr.log').open('w'),creationflags=subprocess.CREATE_NO_WINDOW)
base=None
def api(path,body=None,method=None):
    headers={'Authorization':'Bearer '+service['token']}
    if body is not None:body=json.dumps(body).encode();headers['Content-Type']='application/json'
    with urllib.request.urlopen(urllib.request.Request(base+'/api'+path,data=body,headers=headers,method=method),timeout=120) as response:return json.loads(response.read())
def wait(job):
    previous=None
    for _ in range(4200):
        result=api('/jobs/'+job)
        if result['stage']!=previous:print(result['stage'],flush=True);previous=result['stage']
        if result['status'] not in ('queued','running'):return result
        time.sleep(.5)
    raise AssertionError('Image test exceeded 35 minutes')
try:
    for _ in range(150):
        if (folder/'service.json').is_file():
            service=json.loads((folder/'service.json').read_text());base='http://127.0.0.1:'+str(service['port'])
            try:api('/status');break
            except OSError:pass
        assert process.poll() is None,(folder/'stderr.log').read_text()
        time.sleep(.1)
    request=api('/import',dict(path=str(Path(args.psd).resolve())));assert wait(request['job'])['status']=='completed'
    ident=request['project'];project=api('/projects/'+ident)
    prompt='Refine this exact architectural landscape into a polished photorealistic daylight CG visualization: natural olive-green grass with subtle variation, weathered grey-brown cedar grain, warm off-white mineral walls and believable glass. Preserve the existing architecture, all roof and window shapes, camera, terrain silhouette, paths and all tree positions. Neutral natural lighting, soft restrained contrast. Keep the white background empty. Do not add people, buildings or new vegetation.'
    settings=dict(revision=project['revision'],size=1536,overlap=256,roles={l['id']:'preserve' for l in project['document']['layers']},prompt=prompt)
    api('/projects/'+ident+'/settings',settings,'PUT')
    bad=api('/projects/'+ident+'/generate',dict(revision=1,mode='tile',tileId=1))
    failure=wait(bad['job']);assert failure['status']=='failed' and '没有可修改' in failure['stage'],failure
    assert not list((folder/'projects'/ident/'runs'/bad['run']).rglob('events.jsonl')),'Read-only job called a model'
    cancelled=api('/projects/'+ident+'/generate',dict(revision=1,mode='all'))
    api('/jobs/'+cancelled['job']+'/cancel',{})
    assert api('/jobs/'+cancelled['job'])['status']=='cancelled'
    for attempt in range(100):
        try:
            resumed=api('/projects/'+ident+'/runs/'+cancelled['run']+'/resume',{})
            break
        except urllib.error.HTTPError as error:
            assert error.code==409,error.read()
            time.sleep(.1)
    assert wait(resumed['job'])['status']=='failed'
    assert not list((folder/'projects'/ident/'runs'/cancelled['run']).rglob('events.jsonl')),'Cancelled read-only job called a model'
    roles={l['id']:('preserve' if l['name'] in ('植物','Betula nigra') else 'reference' if l['name'] in ('Shadow','Arctic') else 'generate') for l in project['document']['layers']}
    settings.update(revision=1,roles=roles);api('/projects/'+ident+'/settings',settings,'PUT')
    receipt=dict(folder=str(folder),project=ident,noEditablePreflight=True,cancelAndResume=True)
    if args.images:
        request=api('/projects/'+ident+'/generate',dict(revision=2,mode='tile',tileId=1))
        receipt.update(run=request['run'],job=request['job']);(folder/'request.json').write_text(json.dumps(receipt,indent=2))
        job=wait(request['job']);state=api('/projects/'+ident+'/runs/'+request['run'])
        assert job['status']=='completed',state
        assert state['style'] and any(t['status'] in ('completed','review') and t.get('receipt',{}).get('newImage') for t in state['tiles']),state
        receipt.update(status=state['status'],state=state)
    (folder/'verified.json').write_text(json.dumps(receipt,indent=2))
    print(json.dumps({k:v for k,v in receipt.items() if k!='state'}),flush=True)
finally:
    if not args.keep and base:
        try:api('/shutdown',{});process.wait(10)
        except Exception:
            if process.poll() is None:process.terminate()

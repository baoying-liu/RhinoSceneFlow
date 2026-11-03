"""Real HTTP + PSD integration. Optional --chat invokes logged-in local Codex (text only)."""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--psd', required=True)
parser.add_argument('--codex', default='')
parser.add_argument('--chat', action='store_true')
parser.add_argument('--keep', action='store_true')
args = parser.parse_args()
evidence = ROOT/'artifacts'/'postproduction'/uuid.uuid4().hex
evidence.mkdir(parents=True)
command = [sys.executable, '-I', '-X', 'utf8', str(ROOT/'src/RhinoSceneFlow.Plugin/PostProduction/server.py'), '--data', str(evidence), '--codex', args.codex]
process = subprocess.Popen(command, stdout=(evidence/'stdout.log').open('w'), stderr=(evidence/'stderr.log').open('w'), creationflags=subprocess.CREATE_NO_WINDOW)
base = None

def request(route, body=None, method=None, auth=True, headers=None):
    actual = {'Authorization': 'Bearer '+record['token']} if auth else {}
    actual.update(headers or {})
    if body is not None:
        body = json.dumps(body).encode()
        actual['Content-Type'] = 'application/json'
    with urllib.request.urlopen(urllib.request.Request(base+route, data=body, headers=actual, method=method), timeout=120) as response:
        data = response.read()
        return json.loads(data) if response.headers.get('Content-Type','').startswith('application/json') else data

def expect_error(status, *a, **kw):
    try:
        request(*a, **kw)
        raise AssertionError('Expected HTTP '+str(status))
    except urllib.error.HTTPError as error:
        assert error.code == status, error.read()

def wait(job):
    for _ in range(600):
        state = request('/api/jobs/'+job)
        if state['status'] not in ('queued','running'):
            assert state['status'] == 'completed', state
            return state
        time.sleep(.25)
    raise AssertionError('Timed out')

try:
    for _ in range(100):
        if (evidence/'service.json').is_file():
            record = json.loads((evidence/'service.json').read_text())
            base = 'http://127.0.0.1:'+str(record['port'])
            try:
                request('/api/status')
                break
            except OSError:
                pass
        assert process.poll() is None, (evidence/'stderr.log').read_text()
        time.sleep(.15)
    assert base
    expect_error(401, '/api/status', auth=False)
    expect_error(403, '/api/status', headers={'Origin':'https://example.com'})
    expect_error(400, '/api/import', {'path':str(evidence/'missing.psd')})
    result = request('/api/import', {'path':str(Path(args.psd).resolve()), 'context':{'documentName':'Fixture'}})
    imported = wait(result['job'])
    ident = result['project']
    project = request('/api/projects/'+ident)
    assert project['status'] == 'ready' and project['document']['layers']
    assert project['document']['sha256'] == hashlib.sha256(Path(args.psd).read_bytes()).hexdigest()
    assert len(request('/api/projects/'+ident+'/media/preview.png')) > 100
    settings = dict(revision=0, size=1024, overlap=128, roles={l['id']:'preserve' for l in project['document']['layers']}, prompt='保留建筑几何，柔和水彩')
    request('/api/projects/'+ident+'/settings', settings, 'PUT')
    expect_error(409, '/api/projects/'+ident+'/settings', settings, 'PUT')
    plan = request('/api/projects/'+ident+'/plan')
    assert all(l['role']=='preserve' for l in plan['layers'])
    assert not plan['generationExecuted']
    area = 0
    for tile in plan['tiles']:
        x,y,r,b = tile['core']; l,t,right,bottom = tile['context']
        area += (r-x)*(b-y)
        assert 0 <= l <= x < r <= right <= plan['width']
        assert 0 <= t <= y < b <= bottom <= plan['height']
        assert right-l <= 1024 and bottom-t <= 1024
    assert area == plan['width'] * plan['height']
    # Prove cores do not overlap, not just equality of their aggregate area.
    for i,a in enumerate(plan['tiles']):
        for b in plan['tiles'][i+1:]:
            ax,ay,ar,ab=a['core'];bx,by,br,bb=b['core']
            assert min(ar,br)<=max(ax,bx) or min(ab,bb)<=max(ay,by)
    assert request('/api/projects/'+ident+'/download') == plan
    expect_error(404, '/api/projects/'+ident+'/media/source.psd')
    # Browser file-picker uploads use a separate HTTP path from the Rhino path handoff.
    boundary = uuid.uuid4().hex
    payload = ('--'+boundary+'\r\nContent-Disposition: form-data; name="file"; filename="uploaded.psd"\r\nContent-Type: application/octet-stream\r\n\r\n').encode()+Path(args.psd).read_bytes()+('\r\n--'+boundary+'--\r\n').encode()
    upload_request=urllib.request.Request(base+'/api/upload',data=payload,headers={'Authorization':'Bearer '+record['token'],'Content-Type':'multipart/form-data; boundary='+boundary})
    with urllib.request.urlopen(upload_request,timeout=120) as response:
        uploaded=json.loads(response.read())
    wait(uploaded['job'])
    assert request('/api/projects/'+uploaded['project'])['document']['sha256']==project['document']['sha256']
    if args.chat:
        job = request('/api/projects/'+ident+'/chat', {'message':'请给出简短水彩建筑后期描述，保持所有几何和植物位置。','includePreview':True})
        completed=wait(job['id'])
        assert completed['result']['text'] and completed['result']['prompt']
        assert len(request('/api/projects/'+ident)['messages'])==2
        (evidence/'chat-result.json').write_text(json.dumps(completed,ensure_ascii=False,indent=2),encoding='utf-8')
    # Restart the service in the same data root, proving project/config/chat persistence.
    if not args.keep:
        request('/api/shutdown', {}, 'POST');process.wait(10)
        process=subprocess.Popen(command, stdout=(evidence/'restart-stdout.log').open('w'),stderr=(evidence/'restart-stderr.log').open('w'),creationflags=subprocess.CREATE_NO_WINDOW)
        old_pid=record['pid']
        for _ in range(100):
            record=json.loads((evidence/'service.json').read_text())
            if record['pid']!=old_pid:
                base='http://127.0.0.1:'+str(record['port'])
                try:
                    reopened=request('/api/projects/'+ident)
                    break
                except OSError:pass
            time.sleep(.1)
        assert reopened['settings']['prompt']==settings['prompt'] and reopened['revision']==1
        assert len(reopened['messages'])==(2 if args.chat else 0)
    (evidence/'verified.json').write_text(json.dumps(dict(project=ident,dimensions=[plan['width'],plan['height']],layers=len(plan['layers']),tiles=len(plan['tiles']),auth=True,sourceUnchanged=True,conflictGuard=True,partitionExact=True,upload=True,restart=not args.keep,chat=args.chat),indent=2))
    print(json.dumps(dict(evidence=str(evidence),project=ident,layers=len(plan['layers']),tiles=len(plan['tiles']),chat=args.chat)))
finally:
    if not args.keep:
        if base:
            try:
                request('/api/shutdown', {}, 'POST')
                process.wait(10)
            except (OSError,subprocess.TimeoutExpired):
                process.terminate()
        elif process.poll() is None:
            process.terminate()

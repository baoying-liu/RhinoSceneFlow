"""Instruction deletion, eye concurrency and stale-session guards; no image calls."""
import json,sys,copy,urllib.request,urllib.error,io
from pathlib import Path
from psd_tools import PSDImage
ROOT=Path(__file__).resolve().parents[1];f=json.loads((ROOT/'artifacts/guide-layers-latest.json').read_text());out=Path(f['folder']);prefix='/boards/'+f['board'];node=f['original'];base=f"http://127.0.0.1:{f['port']}/api"
def call(p,b=None,method=None,raw=False):
 data=b if isinstance(b,bytes) else json.dumps(b).encode() if b is not None else None
 with urllib.request.urlopen(urllib.request.Request(base+p,data=data,headers={'Authorization':'Bearer workflow-fixture-token','Content-Type':'application/octet-stream' if isinstance(b,bytes) else 'application/json'},method=method),timeout=90) as r:return r.read() if raw else json.load(r)
def board():return call(prefix)
def current():return next(x for x in board()['nodes'] if x['id']==node)
def start():return call(prefix+'/nodes/'+node+'/edit-reference/session',dict(revision=board()['revision']))['session']
def reject(fn):
 try:fn()
 except urllib.error.HTTPError as e:assert e.code==409,e.read()
 else:raise AssertionError('Expected stale-session rejection')
before=copy.deepcopy(current());sid=start();data=call(prefix+'/edit-reference/'+sid+'/input',raw=True);a=next(a for a in current()['annotations'] if a['id']==f['mark']);visible=a.get('visible',True)
call(prefix+'/nodes/'+node+'/guide-control',dict(revision=board()['revision'],scope='item',field='visible',value=not visible,layer=f['mark']))
call(prefix+'/edit-reference/'+sid+'/apply',data);assert next(a for a in current()['annotations'] if a['id']==f['mark']).get('visible',True)==(not visible),'Unchanged PSD eye must not overwrite a newer page eye'
sid=start();psd=PSDImage.open(io.BytesIO(call(prefix+'/edit-reference/'+sid+'/input',raw=True)));layer=next(l for l in psd.descendants() if l.name.startswith('[SF:arrow:'));layer.parent.remove(layer);file=out/'delete-instruction.psd';psd.save(file);call(prefix+'/edit-reference/'+sid+'/apply',file.read_bytes());assert not any(a['id']==f['mark'] for a in current()['annotations'])
slot=current()['editReference'];call(prefix+'/history',dict(revision=board()['revision'],direction='undo'));assert any(a['id']==f['mark'] for a in current()['annotations']);assert current()['editReference']==slot
call(prefix+'/history',dict(revision=board()['revision'],direction='redo'));assert not any(a['id']==f['mark'] for a in current()['annotations'])
call(prefix+'/history',dict(revision=board()['revision'],direction='undo'));assert any(a['id']==f['mark'] for a in current()['annotations'])
call(prefix,dict(revision=board()['revision'],nodes=[dict(id=node,annotations=before['annotations'])]),'PUT')
sid=start();data=call(prefix+'/edit-reference/'+sid+'/input',raw=True);marks=copy.deepcopy(current()['annotations']);marks[0]['size']+=1
call(prefix,dict(revision=board()['revision'],nodes=[dict(id=node,annotations=marks)]),'PUT');reject(lambda:call(prefix+'/edit-reference/'+sid+'/apply',data));assert current()['annotations']==marks
call(prefix,dict(revision=board()['revision'],nodes=[dict(id=node,annotations=before['annotations'])]),'PUT')
assert current()['asset']==before['asset'] and current()['versions']==before['versions']
report=dict(individualDeleteSynced=True,specialDeleteUndoRedo=True,appearanceSlotOutsideUndo=True,eyeChangesDuringEditorPreserved=True,staleContentRejected=True,sourceAndBackupsUnchanged=True,modelCalls=0,folder=str(out));(out/'guide-guards-verified.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))

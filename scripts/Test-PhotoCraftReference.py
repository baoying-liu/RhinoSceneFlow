"""After the real browser test: pixel/project oracles, slot guards and package roundtrip."""
import copy,json,sys,uuid,shutil,struct,urllib.request,urllib.error,io
from psd_tools import PSDImage
from pathlib import Path
from PIL import Image
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/RhinoSceneFlow.Plugin/PostProduction'))
from board_store import Store
from board_api import BoardApi
from board_render import prepare
from project import write_json
import canvas_context as context

f=json.loads((ROOT/'artifacts/workflow021-http-latest.json').read_text());browser=json.loads((Path(f['folder'])/'photocraft-browser-verified.json').read_text())
out=ROOT/'artifacts/photocraft-reference'/uuid.uuid4().hex;out.mkdir(parents=True)
base=f"http://127.0.0.1:{f['port']}/api";headers={'Authorization':'Bearer workflow-fixture-token'}
def call(path,body=None,method=None,raw=False):
    data=body if isinstance(body,bytes) else json.dumps(body).encode() if body is not None else None
    with urllib.request.urlopen(urllib.request.Request(base+path,data=data,headers={**headers,'Content-Type':'application/octet-stream' if isinstance(body,bytes) else 'application/json'},method=method),timeout=30) as response:
        data=response.read();return data if raw else json.loads(data)
def reject(fn,status):
    try:fn()
    except urllib.error.HTTPError as e:assert e.code==status,(e.code,e.read())
    else:raise AssertionError('Expected rejection')
prefix='/boards/'+f['board'];node=f['original']
def board():return call(prefix)
def current():return next(n for n in board()['nodes'] if n['id']==node)
def session():return call(prefix+'/nodes/'+node+'/edit-reference/session',dict(revision=board()['revision']))['session']
def apply(sid,project):return call(prefix+'/edit-reference/'+sid+'/apply',project)
old=current();history=board()['historyState'];slot=old['editReference']
source=call(prefix+'/assets/'+old['asset'],raw=True);(out/'source.png').write_bytes(source)
images=[np.asarray(Image.open(Path(f['folder'])/('photocraft-reference-'+str(i)+'.png')).convert('RGBA')) for i in (1,2)]
a=np.asarray(Image.open(out/'source.png').convert('RGBA'));counts=[int(np.count_nonzero(np.any(im[:,:,:3]!=a[:,:,:3],axis=2))) for im in images]
assert counts[1]>counts[0]>300,counts
assert all(np.array_equal(im[0,0],a[0,0]) for im in images),'Unpainted source must retain its colour'
projects=[call(prefix+'/assets/'+s['project'],raw=True) for s in browser['slots']]
one,two=session(),session()
reopened=PSDImage.open(io.BytesIO(call(prefix+'/edit-reference/'+one+'/input',raw=True)))
assert any(l.name=='SceneFlow Instructions [SF1]' for l in reopened)
prior=PSDImage.open(io.BytesIO(projects[1]));assert [l.name for l in reopened if l.name!='SceneFlow Instructions [SF1]']==[l.name for l in prior if l.name!='SceneFlow Instructions [SF1]'],'Preserve editable ordinary layers while refreshing SF instructions'
apply(one,projects[0]);reject(lambda:apply(two,projects[1]),409)
restore=session();apply(restore,projects[1]);reject(lambda:apply(restore,projects[1]),409)
invalid=session();reject(lambda:apply(invalid,struct.pack('>4sH6sHIIHH',b'8BPS',1,b'\0'*6,4,1,9000,8,3)),400)
assert current()['editReference']['project']==slot['project']
local_file=Path(f['folder'])/'boards'/f['board']/'assets'/slot['project'];local_bytes=local_file.read_bytes();local_session=session();call(prefix+'/edit-reference/'+local_session+'/apply-file',dict(path=str(local_file)));assert local_file.read_bytes()==local_bytes
cancel=session();call(prefix+'/edit-reference/'+cancel,method='DELETE');reject(lambda:call(prefix+'/edit-reference/'+cancel+'/input'),404)
assert current()['asset']==old['asset'] and current()['versionId']==old['versionId'] and current()['versions']==old['versions']
assert board()['historyState']==history,'Reference saves must not add undo or backup entries'

# Work only on a copied synthetic board for history, stale-input and raster tests.
(out/'boards').mkdir();shutil.copytree(Path(f['folder'])/'boards'/f['board'],out/'boards'/f['board'])
store=Store(out);bid=f['board'];b=store.read(bid);n=next(n for n in b['nodes'] if n['id']==node)
ref=copy.deepcopy(n['editReference']);b['name']='Rename';store.commit(b)
b=store.history(bid,dict(revision=store.read(bid)['revision'],direction='undo'));assert next(n for n in b['nodes'] if n['id']==node)['editReference']==ref
assert 'editReference' not in json.dumps(store.edit_history(bid))
api=BoardApi(out,{},None);snapshot=api.snapshot(bid,f['child']);assert snapshot['image']==str(store.asset(bid,next(n for n in b['nodes'] if n['id']==f['child'])['asset']))
guide=next(r for r in snapshot['references'] if r.get('editingReference'));assert guide['node']['asset']==ref['asset'] and guide['node']['params']['referencePurpose']=='edited-target'
worker=out/'raster';worker.mkdir();write_json(worker/'snapshot.json',snapshot);prepare(worker)
assert np.array_equal(np.asarray(Image.open(worker/'base.png').convert('RGBA')),np.asarray(Image.open(snapshot['image']).convert('RGBA'))),'Reference must not replace clean input'
assert (worker/'reference-sheet.png').is_file()
pack=store.package(bid);restored=store.unpack(pack);rn=next(n for n in restored['nodes'] if n['id']==node);assert rn['editReference']==ref and store.asset(restored['id'],ref['project']).read_bytes()==projects[1]
changed=store.read(bid);cn=next(n for n in changed['nodes'] if n['id']==node);cn['asset']=next(n for n in changed['nodes'] if n['id']==f['child'])['asset'];store.commit(changed,record=False)
assert not context.live_reference(next(n for n in store.read(bid)['nodes'] if n['id']==node))
report=dict(realBrowserEvidence=browser['folder'],paintedPixels=counts,editableOrdinaryLayersReopened=True,staleSessionRejected=True,repeatedApplyRejected=True,invalidPSDRejected=True,cancelSessionRemoved=True,jsonMcpFileApply=True,singleSlotOutsideHistory=True,sourceAndVersionsPreserved=True,cleanInputNotOverwritten=True,generationReferenceSheet=True,packageRoundTrip=True,changedSourceDisablesOldReference=True,modelCalls=0,folder=str(out))
(out/'verified.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))

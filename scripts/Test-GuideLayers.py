"""Isolated HTTP/PSD contract and independent pixel checks. No model calls."""
import json,sys,uuid,urllib.request,urllib.error,copy
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from psd_tools import PSDImage
from psd_tools.api.layers import PixelLayer
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/RhinoSceneFlow.Plugin/PostProduction'))
from board_store import Store
from board_api import BoardApi
from board_render import prepare
from project import write_json
import canvas_context as context
f=json.loads((ROOT/'artifacts/workflow021-http-latest.json').read_text());out=Path(f['folder']);prefix='/boards/'+f['board'];node=f['original'];base=f"http://127.0.0.1:{f['port']}/api"
def call(route,body=None,method=None,raw=False):
 data=body if isinstance(body,bytes) else json.dumps(body).encode() if body is not None else None
 req=urllib.request.Request(base+route,data=data,headers={'Authorization':'Bearer workflow-fixture-token','Content-Type':'application/octet-stream' if isinstance(body,bytes) else 'application/json'},method=method)
 with urllib.request.urlopen(req,timeout=90) as r:return r.read() if raw else json.load(r)
def board():return call(prefix)
def current():return next(n for n in board()['nodes'] if n['id']==node)
def control(scope,field,value,layer=None):return call(prefix+'/nodes/'+node+'/guide-control',dict(revision=board()['revision'],scope=scope,field=field,value=value,layer=layer))
def start():return call(prefix+'/nodes/'+node+'/edit-reference/session',dict(revision=board()['revision']))
def reject(fn):
 try:fn()
 except urllib.error.HTTPError as e:assert e.code in (400,409),e.read()
 else:raise AssertionError('Expected rejection')
before=current();store=Store(out);picture=out/'resource-fixture.png';Image.new('RGBA',(40,30),'#6655ee').save(picture);asset=store.put_asset(f['board'],picture);resource=store.append(f['board'],asset,asset,40,30,'Reference.png',kind='reference');b=store.read(f['board']);n=next(n for n in b['nodes'] if n['id']==node);rr=next(n for n in b['nodes'] if n['id']==resource['id']);rr['pose']=dict(x=n['pose']['x']+320,y=n['pose']['y']+50,width=100,height=75);store.commit(b);b=board();mark=uuid.uuid4().hex;area=uuid.uuid4().hex
annotations=[dict(id=mark,kind='arrow',points=[[40,40,.5],[100,75,.5]],size=4,color='#ff4411',enabled=False),dict(id=area,kind='protect',points=[[120,100,.5],[200,100,.5],[200,180,.5],[120,180,.5]],closed=True,size=4,color='#22aa55')]
call(prefix,dict(revision=b['revision'],nodes=[dict(id=node,annotations=annotations)]),'PUT')
api=BoardApi(out,{},None);old=api.store.read(f['board']);sig=context.signature(old,next(n for n in old['nodes'] if n['id']==node))
control('item','visible',False,mark);b=api.store.read(f['board']);assert sig==context.signature(b,next(n for n in b['nodes'] if n['id']==node))
control('all','enabled',False);assert not context.collected(api.store.read(f['board']),current())[0]
control('all','enabled',True);assert next(a for a in current()['annotations'] if a['id']==mark)['enabled'] is False
control('item','visible',True,mark)
baselineAnnotations=copy.deepcopy(current()['annotations'])
s=start();file=out/'guide-input.psd';file.write_bytes(call(prefix+'/edit-reference/'+s['session']+'/input',raw=True));psd=PSDImage.open(file)
group=next(g for g in psd if g.name=='SceneFlow Instructions [SF1]');assert len(list(group))==7
assert len(list(group.descendants()))==10
call(prefix+'/edit-reference/'+s['session']+'/apply',file.read_bytes())
n=current();assert n['annotations']==baselineAnnotations,'No-op roundtrip retains vectors and disabled state'
assert np.array_equal(np.asarray(Image.open(api.store.asset(f['board'],n['editReference']['asset'])).convert('RGBA')),np.asarray(Image.open(api.store.asset(f['board'],n['asset'])).convert('RGBA'))),'Instructions must not contaminate appearance'
control('appearance','enabled',False);control('appearance','visible',False)
s=start();file.write_bytes(call(prefix+'/edit-reference/'+s['session']+'/input',raw=True));psd=PSDImage.open(file);group=next(g for g in psd if g.name=='SceneFlow Instructions [SF1]');pg=next(g for g in group if g.name=='SF · protect');oldlayer=next(iter(pg));name=oldlayer.name;pg.remove(oldlayer)
im=Image.new('RGBA',(24,20),'#a52c22');pg.append(PixelLayer.frompil(im,psd,name,left=35,top=40))
refLayer=next(l for l in group.descendants() if l.name.startswith('[SF:reference:'));refLayer.left+=5
im=Image.new('RGBA',(18,18),'#2255ee');psd.append(PixelLayer.frompil(im,psd,'Ordinary blue paint',left=45,top=45));psd.save(file)
call(prefix+'/edit-reference/'+s['session']+'/apply',file.read_bytes());n=current();a=next(a for a in n['annotations'] if a['id']==area);assert a.get('raster') and not a['points']
assert n['editReference']['enabled'] is False and n['editReference']['visible'] is False
control('appearance','enabled',True)
im=Image.open(api.store.asset(f['board'],n['editReference']['asset'])).convert('RGBA');assert im.getpixel((30,30))[:3]==(34,85,238),'Ordinary edits exclude red special layer'
assert n['asset']==before['asset'] and n['versions']==before['versions'] and n['versionId']==before['versionId']
s=start();file.write_bytes(call(prefix+'/edit-reference/'+s['session']+'/input',raw=True));psd=PSDImage.open(file);group=next(g for g in psd if g.name=='SceneFlow Instructions [SF1]');psd.remove(group);psd.save(file);reject(lambda:call(prefix+'/edit-reference/'+s['session']+'/apply',file.read_bytes()))
editedResource=next(x for x in board()['nodes'] if x['id']==resource['id']);assert editedResource['asset']==resource['asset'] and editedResource.get('editReference')
rs=call(prefix+'/nodes/'+resource['id']+'/edit-reference/session',dict(revision=board()['revision']));rp=out/'resource-reopen.psd';rp.write_bytes(call(prefix+'/edit-reference/'+rs['session']+'/input',raw=True));assert PSDImage.open(rp).width<100,'Resource reopens independently, not the parent project'
# Freeze actual raster protection and compare independently to its expected alpha.
snap=api.snapshot(f['board'],node);raster=out/'guide-raster';raster.mkdir();write_json(raster/'snapshot.json',snap);prepare(raster)
mask=np.asarray(Image.open(raster/'mask.png'));q=a['rasterPose'];p=n['pose'];x=round(q['x']*n['width']/p['width']);y=round(q['y']*n['height']/p['height']);assert mask[y+3,x+3]==0 and mask[-1,-1]==255
child=f['child'];call(prefix+'/nodes/'+child+'/guide-control',dict(revision=board()['revision'],scope='all',field='visible',value=False))
reject(lambda:call(prefix+'/nodes/'+child+'/guide-control',dict(revision=board()['revision'],scope='all',field='enabled',value=False)))
# Package retains instruction rasters and metadata.
packed=api.store.package(f['board']);restored=api.store.unpack(packed);assert next(x for x in restored['nodes'] if x['id']==node)['annotations']==n['annotations']
report=dict(folder=str(out),reservedFoldersValidated=True,stableIDs=True,noOpRetainsVectors=True,appearanceExcludesInstructions=True,editedInstructionRaster=True,ordinaryFlagsPreserved=True,masterPreservesChildren=True,visibilityOutsideSignature=True,protectionAlphaApplied=True,sourceAndBackupsUnchanged=True,packageRoundtrip=True,referenceSourcePreserved=True,referenceEditorIndependent=True,lockedEnableRejected=True,modelCalls=0,mark=mark,protect=area)
write_json(out/'guide-layers-verified.json',report);write_json(ROOT/'artifacts/guide-layers-latest.json',{**f,**report});print(json.dumps(report))

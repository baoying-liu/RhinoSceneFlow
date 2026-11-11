"""Actual PSD pixels and model-attachment contract; no real image model calls."""
import asyncio,copy,hashlib,json,sys,uuid
from pathlib import Path
from PIL import Image
import numpy as np
from psd_tools import PSDImage
from psd_tools.api.layers import PixelLayer,Group
from psd_tools.constants import BlendMode

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src/RhinoSceneFlow.Plugin/PostProduction'))
import project,board_render,psd_guides
from board_store import Store,params
from board_api import BoardApi

out=ROOT/'artifacts/psd-participation'/uuid.uuid4().hex;out.mkdir(parents=True)
psd=PSDImage.new('RGBA',(96,72))
psd.append(PixelLayer.frompil(Image.new('RGBA',(96,72),'#58934d'),psd,'Ground'))
overlay=Image.new('RGBA',(96,72));overlay.paste('#b85742',(12,16,39,55))
psd.append(PixelLayer.frompil(overlay,psd,'Facade'))
depth=np.zeros((72,96,4),dtype=np.uint8);depth[:,:,:3]=np.arange(96,dtype=np.uint8)[None,:,None]*2;depth[:,:,3]=255
hidden=PixelLayer.frompil(Image.fromarray(depth),psd,'Depth');hidden.visible=False;psd.append(hidden)
color=PixelLayer.frompil(Image.new('RGBA',(96,72),'#2187df'),psd,'Material colors');color.visible=False;psd.append(color)
psd.save(out/'source.psd');project.prepare(out)
doc=project.read_json(out/'document.json');rows=doc['layers'];by_name={l['name']:l['id'] for l in rows}
source_hash=hashlib.sha256((out/'source.psd').read_bytes()).hexdigest()
canonical=np.array(Image.open(out/'composite.png').convert('RGBA'))
base=params(dict(prompt='Refine real wood and grass',edgeGuard=0))
snapshot=dict(image=str(out/'composite.png'),psd=str(out/'source.psd'),layers=rows,references=[],node=dict(params=base,pose=dict(x=0,y=0,width=96,height=72),frame=dict(x=0,y=0,width=96,height=72),annotations=[]))

def prepare(name,settings):
    folder=out/name;folder.mkdir();s=copy.deepcopy(snapshot);s['node']['params'].update(settings)
    project.write_json(folder/'snapshot.json',s);board_render.prepare(folder)
    return folder,project.read_json(folder/'prepared.json')

default=psd_guides.settings(rows,base)
assert all(l['participates']==l['effectiveVisible'] for l in default)
normal,info=prepare('default',{});assert not info['guides']
assert np.array_equal(canonical,np.array(Image.open(normal/'base.png')))
on={by_name['Depth']:True}
guides,ginfo=prepare('depth-enabled',dict(layerParticipation=on))
assert [g['kind'] for g in ginfo['guides']]==['depth']
assert np.array_equal(np.array(Image.open(guides/'base.png')),canonical)
assert np.array_equal(np.array(Image.open(guides/'mask.png')),np.array(Image.open(normal/'mask.png')))
assert len(np.unique(np.asarray(Image.open(guides/'psd-guides.png'))))>60
assert hashlib.sha256((out/'source.psd').read_bytes()).hexdigest()==source_hash
assert not PSDImage.open(out/'source.psd')[-1].visible
parent=dict(id='g',name='Hidden channels',parent=None,visible=False,effectiveVisible=False,group=True)
childrow=dict(rows[2],parent='g')
assert not psd_guides.settings([parent,childrow],dict(layerParticipation={childrow['id']:True}))[1]['participates'],'Hidden parent must gate child'

off,off_info=prepare('facade-off',dict(layerParticipation={by_name['Facade']:False}))
mask=np.array(Image.open(off/'mask.png'));assert not np.any(mask[16:55,12:39]);assert np.any(mask[:12,:])
Image.new('RGB',(1536,1536),'#81b8ce').save(off/'generated.png');board_render.finish(off)
result=np.array(Image.open(off/'result.png'));assert np.array_equal(result[16:55,12:39],canonical[16:55,12:39])
assert np.array_equal(result[:,:,3],canonical[:,:,3])
try:prepare('all-off',dict(layerParticipation={l['id']:False for l in rows}))
except ValueError as e:assert '可修改' in str(e) or 'editable' in str(e)
else:raise AssertionError('All-off must reject before a model request')
for bad in ({'1':1},{'1':'false'},[]):
    try:params(dict(layerParticipation=bad))
    except ValueError:pass
    else:raise AssertionError('Non-boolean participation accepted')

# Preflight and real work orchestration both use the owned raster worker, with
# a synthetic image responder that records the exact attachments and prompt.
(out/'http').mkdir();store=Store(out/'http');b=store.create('PSD participation fixture');bid=b['id']
asset=store.put_asset(bid,out/'composite.png');psd_asset=store.put_asset(bid,out/'source.psd','.psd')
root=store.append(bid,asset,asset,96,72,'Architecture.psd',source=dict(psdAsset=psd_asset,layers=rows))
child=store.branch(bid,root['id']);store.patch(bid,dict(revision=store.read(bid)['revision'],nodes=[dict(id=child['id'],params={**child['params'],'prompt':'Refine wood','edgeGuard':0,'layerParticipation':on})]))
calls=[]
class FakeGeneration:
    image_gate=asyncio.Lock()
    async def image(self,job,folder,brief,images):
        calls.append(dict(brief=brief,images=[str(p) for p in images],hashes=[hashlib.sha256(p.read_bytes()).hexdigest() for p in images]))
        folder.mkdir();image=folder/'synthetic.png';Image.new('RGB',(1536,1536),'#79ac68').save(image)
        return image,dict(syntheticFixture=True,sha256=hashlib.sha256(image.read_bytes()).hexdigest())
api=BoardApi(out/'http',dict(new_job=lambda *a:dict(id=uuid.uuid4().hex,status='queued')),FakeGeneration())
async def raster(job,operation,folder):{'prepare':board_render.prepare,'finish':board_render.finish}[operation](folder)
api.raster=raster
async def checks():
    plan=await api.preflight(bid,child['id'],dict(revision=store.read(bid)['revision'],stage='whole'))
    assert set(plan['images'])=={'input','context','mask','guides'} and plan['guides'][0]['kind']=='depth'
    folder=out/'model-contract';folder.mkdir();s=api.generation_snapshot(bid,child['id']);project.write_json(folder/'snapshot.json',s)
    task=dict(id=uuid.uuid4().hex,board=bid,node=child['id'],stage='whole',status='queued');job=dict(id=uuid.uuid4().hex,status='running')
    await api.work(job,folder,task,s)
    assert task['status']=='completed',task
    assert len(calls)==1 and Path(calls[0]['images'][-1]).name=='psd-guides.png'
    assert 'Image 4 is the PSD CHANNEL GUIDE SHEET' in calls[0]['brief']
    assert 'Image 4 is a numbered REFERENCE SHEET' not in calls[0]['brief']
    assert len(calls[0]['images'])==4
    # A generated parent must not reacquire the original coarse PSD channels.
    grandchild=store.branch(bid,child['id']);assert 'psd' not in api.generation_snapshot(bid,grandchild['id'])
asyncio.run(checks())
report=dict(defaultsMatchVisibility=True,hiddenParentGate=True,hiddenDepthActuallyAttached=True,canonicalAndMaskUnchanged=True,disabledVisiblePixelsExact=True,sourcePsdUnchanged=True,allOffRejected=True,attachmentNumbering=True,coarseGuidesNotReapplied=True,syntheticImageCalls=len(calls),realModelCalls=0,folder=str(out))
project.write_json(out/'verified.json',report);project.write_json(out/'recorded-image-request.json',calls)
print(json.dumps(report))

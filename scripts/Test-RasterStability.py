"""Real Hillside PSD preparation + synthetic numeric oracles, zero image-model calls."""
import sys,uuid,shutil,json,copy,hashlib,asyncio
from pathlib import Path
import numpy as np,cv2
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/RhinoSceneFlow.Plugin/PostProduction'))
import project,render,board_render
out=ROOT/'artifacts/raster0222'/uuid.uuid4().hex;out.mkdir(parents=True)
source=ROOT/'artifacts/examples/Hillside-Retreat/PSD/01 Hillside Axon.psd'
shutil.copyfile(source,out/'source.psd');project.prepare(out);doc=project.read_json(out/'document.json')
canonical=np.array(Image.open(out/'composite.png').convert('RGBA'));w,h=doc['width'],doc['height']
params=dict(editScope='auto',blend=100,edgeGuard=1,roles={l['id']:'preserve' for l in doc['layers'] if l['name']=='Betula nigra'})
snap=dict(image=str(out/'composite.png'),psd=str(out/'source.psd'),layers=doc['layers'],references=[],node=dict(params=params,pose=dict(x=0,y=0,width=w,height=h),frame=dict(x=0,y=0,width=w,height=h),annotations=[]))
def prep(name,s):
 p=out/name;p.mkdir();project.write_json(p/'snapshot.json',s);board_render.prepare(p);return p
base=prep('whole',snap);assert np.array_equal(canonical,np.array(Image.open(base/'base.png')))
assert not project.read_json(base/'prepared.json')['sourceAdjusted']
Image.new('RGB',(w,h),'#bf7960').save(base/'generated.png');board_render.finish(base)
mask=np.array(Image.open(base/'mask.png'));result=np.array(Image.open(base/'result.png'))
assert np.array_equal(result[mask==0],canonical[mask==0]);assert np.array_equal(result[:,:,3],canonical[:,:,3])
local=copy.deepcopy(snap);local['node']['params']['editScope']='local'
try:prep('missing-region',local)
except ValueError as e:assert 'closed edit region' in str(e)
else:raise AssertionError('Local mode accepted an empty region')
def polygon(kind,box):
 x,y,r,b=box;return dict(id=uuid.uuid4().hex,kind=kind,closed=True,points=[[x,y,1],[r,y,1],[r,b,1],[x,b,1]],size=2,color='#aa7722')
local['node']['annotations']=[polygon('edit',(420,400,700,620)),polygon('protect',(480,460,540,510))]
lp=prep('local',local);lm=np.array(Image.open(lp/'mask.png'));assert lm[475,510]==0 and lm[500,650]>0 and lm[350,650]==0
whole=copy.deepcopy(local);whole['node']['params']['editScope']='whole';wp=prep('explicit-whole',whole);wm=np.array(Image.open(wp/'mask.png'));assert wm[350,650]>0 and wm[475,510]==0
excluded=copy.deepcopy(snap);excluded['node']['params']['roles']={doc['layers'][-1]['id']:'exclude'};ep=prep('excluded',excluded);assert project.read_json(ep/'prepared.json')['sourceAdjusted'];assert not np.array_equal(canonical,np.array(Image.open(ep/'base.png')))
from board_api import BoardApi
(out/'transport').mkdir();api=BoardApi(out/'transport',dict(new_job=lambda *a:dict(id=uuid.uuid4().hex,status='queued')),None);store=api.store;b=store.create('Prepared input fixture');bid=b['id'];asset=store.put_asset(bid,out/'composite.png');psdasset=store.put_asset(bid,out/'source.psd','.psd');src=store.append(bid,asset,asset,w,h,'Hillside.psd',source=dict(psdAsset=psdasset,layers=doc['layers']));draft=store.branch(bid,src['id']);store.patch(bid,dict(revision=store.read(bid)['revision'],nodes=[dict(id=draft['id'],params={**draft['params'],'prompt':'Test exclude preparation','roles':excluded['node']['params']['roles']})]))
async def raster(job,operation,folder):board_render.prepare(folder)
api.raster=raster
plan=asyncio.run(api.preflight(bid,draft['id'],dict(revision=store.read(bid)['revision'],stage='whole')))
assert plan['sourceAdjusted'] and plan['input']['prepared'] and plan['input']['originalAsset']==asset and plan['input']['asset']!=asset
assert next(n for n in store.read(bid)['nodes'] if n['id']==draft['id'])['input']['asset']==asset
# Exact partition and bounded context, including many awkward aspect ratios.
for ww,hh in [(1024,768),(2048,1536),(1200,900),(901,97),(97,901),(19,17),(4096,2048)]:
 tiles=project.tiles(ww,hh,1024,64);cover=np.zeros((hh,ww),np.uint8)
 for t in tiles:
  x,y,r,b=t['core'];l,top,right,bottom=t['context'];cover[y:b,x:r]+=1
  assert 0<=l<=x<r<=right<=ww and 0<=top<=y<b<=bottom<=hh
  assert max(right-l,bottom-top)<=1024
 assert np.all(cover==1)
tiles=project.tiles(1024,768,1024,64);assert all(t['core'][2]-t['core'][0]==512 and t['context'][2]-t['context'][0]>=768 for t in tiles)
# Optical-flow diagnostics reject a known translation, and do not invent one for colour changes.
rng=np.random.default_rng(77);texture=np.full((320,480,3),210,np.uint8)
for _ in range(130):
 x,y=rng.integers(15,460),rng.integers(15,300);cv2.rectangle(texture,(x,y),(x+10,y+12),tuple(int(v) for v in rng.integers(30,170,3)),-1)
same=np.clip(texture.astype(np.int16)+5,0,255).astype(np.uint8);shift=cv2.warpAffine(texture,np.float32([[1,0,15],[0,1,0]]),(480,320),borderValue=(210,210,210))
assert not render.displacement(texture,same)['review'];assert render.displacement(texture,shift)['review']
# Full coverage must never reintroduce the dark source at overlapping tile edges.
fusion=out/'fusion';fusion.mkdir();Image.new('RGBA',(1024,768),(10,20,30,173)).save(fusion/'base.png');Image.new('L',(1024,768),255).save(fusion/'edit-mask.png')
state=dict(tiles=[],fusionId=uuid.uuid4().hex,colorMatch=False)
for t in tiles:
 l,top,right,bottom=t['context'];file='tile-'+str(t['id'])+'.png';Image.new('RGB',(right-l,bottom-top),(170,180,190)).save(fusion/file);state['tiles'].append(dict(t,status='completed',image=file))
project.write_json(fusion/'run.json',state);report=render.compose(fusion);pixels=np.array(Image.open(fusion/report['image']));assert np.max(np.abs(pixels[:,:,:3].astype(int)-[170,180,190]))<=3;assert np.all(pixels[:,:,3]==173)
overlap=render.overlap_quality(fusion,2);assert not overlap['review']
# Four textured, mutually identical world-space crops must reconstruct their source.
# Constant-colour pairs alone did not expose hard-seam/pyramid boundary artefacts.
textured=out/'textured-four';textured.mkdir();truth=Image.open(out/'composite.png').convert('RGBA').resize((2048,1536),Image.Resampling.LANCZOS);truth.save(textured/'base.png');Image.new('L',truth.size,255).save(textured/'edit-mask.png');rows=[]
for t in project.tiles(2048,1536,1536,128):
 file='tile-'+str(t['id'])+'.png';truth.convert('RGB').crop(t['context']).save(textured/file);rows.append(dict(t,status='completed',image=file))
project.write_json(textured/'run.json',dict(tiles=rows,fusionId=uuid.uuid4().hex,colorMatch=False));rep=render.compose(textured);difference=np.abs(np.array(Image.open(textured/rep['image']).convert('RGB')).astype(int)-np.array(truth.convert('RGB')).astype(int));assert difference.max()<=12 and np.percentile(difference,99)<=6
v=dict(realHillsideCanonicalExact=True,sourceAlphaExact=True,localRequiresClosedRegion=True,wholeIgnoresEditButPreservesProtection=True,excludedCompositeDistinct=True,actualPreparedInputPinned=True,historicalInputUnchanged=True,balancedCores=True,boundedContext=True,geometryShiftDetected=True,noOldBaseGhostAtFullCoverage=True,texturedFourTileReconstruction=True,overlapConsistency=True,modelCalls=0,folder=str(out))
project.write_json(out/'verified.json',v);print(json.dumps(v))

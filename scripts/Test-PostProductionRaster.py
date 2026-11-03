"""Independent synthetic pixel oracles; these candidates are fixtures, never claimed AI outputs."""
import sys,json,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src/RhinoSceneFlow.Plugin/PostProduction'))
import project,render
import numpy as np
from PIL import Image,ImageDraw
from psd_tools import PSDImage
from psd_tools.api.layers import PixelLayer

folder=ROOT/'artifacts/postproduction-raster'/uuid.uuid4().hex
folder.mkdir(parents=True)
w,h=700,420
psd=PSDImage.new('RGBA',(w,h))
def layer(name,color,box):
    image=Image.new('RGBA',(w,h),(0,0,0,0));ImageDraw.Draw(image).rectangle(box,fill=color)
    entry=PixelLayer.frompil(image,psd,name);psd.append(entry);return entry
layer('reference background',(245,245,245,255),(0,0,w,h))
layer('editable building',(80,110,140,255),(80,60,620,360))
layer('preserve plant',(30,150,70,128),(170,110,240,270))
layer('excluded marker',(255,0,255,255),(300,160,350,220))
psd.save(folder/'source.psd');project.prepare(folder)
doc=json.loads((folder/'document.json').read_text())
roles={'reference background':'reference','editable building':'generate','preserve plant':'preserve','excluded marker':'exclude'}
rows=[dict(row,role=roles[row['name']]) for row in doc['layers']]
run=folder/'runs'/uuid.uuid4().hex;run.mkdir(parents=True)
snapshot=dict(sourceSha256=doc['sha256'],layers=rows,width=w,height=h,tileSize=512,edgeGuard=1,
              tiles=project.tiles(w,h,512,64))
project.write_json(run/'snapshot.json',snapshot);render.prepare(run)
base=np.asarray(Image.open(run/'base.png'));mask=np.asarray(Image.open(run/'edit-mask.png'))
assert mask[200,200]==0,'preserved alpha-edge pixels must be protected'
assert mask[100,100]>0 and mask[10,10]==0
assert tuple(base[180,320,:3])==(80,110,140),'excluded layer leaked into base'
assert mask[60,100]==0,'silhouette guard failed'
state=dict(tiles=[],colorMatch=True,fusionId=uuid.uuid4().hex)
for tile in snapshot['tiles']:
    directory=run/('tile-'+str(tile['id']))
    if not directory.exists():continue
    placement=json.loads((directory/'placement.json').read_text())
    x,y=placement['offset'];tw,th=placement['width'],placement['height']
    # Realistic integer fixture: constant appearance change, identical scene geometry.
    image=np.asarray(Image.open(directory/'input.png').convert('RGB')).copy()
    image=np.clip(image.astype(np.int16)+20,0,255).astype(np.uint8)
    Image.fromarray(image[y:y+th,x:x+tw]).save(directory/'fixture.png')
    state['tiles'].append(dict(tile,status='completed',image='tile-'+str(tile['id'])+'/fixture.png'))
project.write_json(run/'run.json',state);report=render.compose(run)
out=np.asarray(Image.open(run/report['image']))
assert out.shape==base.shape
assert np.array_equal(out[mask==0],base[mask==0]),'read-only pixels changed'
assert np.array_equal(out[:,:,3],base[:,:,3]),'source alpha changed'
assert report['changedPixels']>50000
# No seam stripes on a uniform material across horizontal and vertical tile boundaries.
valid=(mask==255)&(base[:,:,0]==80)
error=np.abs(out[:,:,:3].astype(int)-np.clip(base[:,:,:3].astype(int)+20,0,255))
assert np.percentile(error[valid],95)<=3,(np.percentile(error[valid],95),error[valid].max())
state['tiles']=state['tiles'][:1];state['fusionId']=uuid.uuid4().hex
project.write_json(run/'run.json',state);partial=render.compose(run)
trial=np.asarray(Image.open(run/partial['image']))
assert np.array_equal(trial[mask==0],base[mask==0])
assert np.array_equal(trial[100,600],base[100,600]),'single-block trial altered far outside its context'
verified=dict(dimensions=[w,h],exactReadonly=True,exactAlpha=True,excluded=True,guard=True,changedPixels=report['changedPixels'],uniformFusionP95=float(np.percentile(error[valid],95)),trialBounded=True)
project.write_json(folder/'verified.json',verified)
print(json.dumps(dict(folder=str(folder),**verified)))

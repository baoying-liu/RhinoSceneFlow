"""Independent PSD decode and compositor; run in artifacts/verify-env."""
import json
from pathlib import Path
import numpy as np
from PIL import Image
from psd_tools import PSDImage
root=Path(__file__).resolve().parents[1];folder=root/'artifacts/rhino-B/textures'
checks=[]
def verify(path,children=None,allTextured=True):
 psd=PSDImage.open(path);group=next(l for l in psd if l.name=='材质')
 assert group.is_group() and len(group)>0
 if children is not None:assert len(group)==children,(path,len(group),children)
 for layer in group:
  assert not layer.is_group(),'Object layers belong directly to one material Group'
  im=np.array(layer.topil().convert('RGBA'));opaque=im[:,:,3]>128
  assert not allTextured or np.unique(im[:,:,:3][opaque],axis=0).shape[0]>30,'Textures collapsed to a solid material color'
 a=np.array(psd.topil().convert('RGBA')).astype(float);b=np.array(psd.composite(force=True).convert('RGBA')).astype(float)
 a[:,:,:3]*=a[:,:,3:]/255;b[:,:,:3]*=b[:,:,3:]/255
 error=float(abs(a-b).max());assert error<4,(path,error)
 checks.append(dict(path=str(path),children=[l.name for l in group],maxPremultipliedError=error))
 psd.topil().save(Path(path).with_suffix('.png'))
 return psd,np.array(psd.topil().convert('RGBA'))
for mode,count in [('material',2),('object',3)]:verify(root/'artifacts/validation'/('texture-'+mode+'.psd'),allTextured=False)
report=json.loads((folder/'report.json').read_text('utf-8'));assert report['complete'] and report['stateUnchanged']
camera=report['topCamera'];origin=np.array(camera['origin']);right=np.array(camera['right']);up=np.array(camera['up']);back=np.array(camera['back'])
left,rightEdge,bottom,top,near,far=camera['frustum'];uv0,uvx,uvy=np.array(report['uvBasis']);basePoint=np.array(report['planeOrigin']);scale=report['unitsPerMeter']
source=np.array(Image.open(report['source']).convert('RGB'));sh,sw=source.shape[:2]
def sample(uv):
 u,v=uv[:2]%1;x=u*sw-.5;y=(1-v)*sh-.5;ix=int(np.floor(x));iy=int(np.floor(y));fx=x-ix;fy=y-iy
 return np.rint((source[iy%sh,ix%sw]*(1-fx)+source[iy%sh,(ix+1)%sw]*fx)*(1-fy)+(source[(iy+1)%sh,ix%sw]*(1-fx)+source[(iy+1)%sh,(ix+1)%sw]*fx)*fy)
topPixels=np.array(PSDImage.open(report['exports']['material']['files'][0]['path']).topil().convert('RGBA'));pixelErrors=[]
for y in range(0,256,3):
 for x in range(0,384,3):
  expected=[]
  for sy in range(2):
   for sx in range(2):
    start=origin+right*(left+(rightEdge-left)*(x+(sx+.5)/2)/384)+up*(top-(top-bottom)*(y+(sy+.5)/2)/256)
    hit=start-back*(start[2]/back[2]);delta=(hit-basePoint)/scale
    if .05<delta[0]<1.75 and .05<delta[1]<1.15:expected.append(sample(uv0+(uvx-uv0)*delta[0]+(uvy-uv0)*delta[1]))
  if len(expected)==4:pixelErrors.append(float(abs(np.rint(np.mean(expected,axis=0))-topPixels[y,x,:3]).max()))
assert len(pixelErrors)>100 and max(pixelErrors)<=2,(len(pixelErrors),max(pixelErrors,default=-1))
for i in range(2):
 merged,a=verify(report['exports']['material']['files'][i]['path'],2)
 split,b=verify(report['exports']['object']['files'][i]['path'],6)
 assert np.array_equal(a,b),'Material/object grouping must produce identical composite bytes'
 # Distinct actual materials with identical labels remain separate.
 assert merged[0][0].name==merged[0][1].name
sun,c=verify(report['exports']['sun']['files'][0]['path'],6)
_,base=verify(report['exports']['object']['files'][0]['path'],6);assert np.array_equal(base,c),'Albedo must ignore sun lighting'
shadow,_=verify(report['exports']['shadow']['files'][0]['path'],2)
assert shadow[-1].name=='Shadow' and shadow[-1].blend_mode.value==b'mul ' and shadow[-1].opacity==166
classic,rgb=verify(report['exports']['classic']['files'][0]['path'],len(set(report['classicEffectiveIndices'])),allTextured=False)
assert np.count_nonzero(rgb[:,:,3]==255)>100
assert np.all(rgb[:,:,:3][rgb[:,:,3]==255]==[43,93,167]),'Classic material must use its actual inherited diffuse color'
result=dict(ok=True,pid=report['pid'],groupingCompositeExact=True,unlitSunInvariant=True,classicMaterialCorrect=True,physicalScalePixelOracle=dict(samples=len(pixelErrors),maxError=max(pixelErrors)),checks=checks)
(folder/'verified.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),'utf-8');print(json.dumps(result,ensure_ascii=True))


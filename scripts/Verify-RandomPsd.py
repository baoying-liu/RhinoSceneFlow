"""Independent psd-tools/Pillow decode against actual native cached PNG + metric UV."""
from pathlib import Path
import json,numpy as np
from PIL import Image
from psd_tools import PSDImage
root=Path(__file__).resolve().parents[1];folder=root/'artifacts/rhino-B/random014'
obj=json.loads((folder/'object-export.json').read_text());stochastic=json.loads((folder/'stochastic-export.json').read_text())
def decode(report,count):
 path=report['files'][0]['path'];psd=PSDImage.open(path);group=next(l for l in psd if l.is_group() and l.name=='材质');assert len(group)==count,(len(group),count)
 array=np.array(psd.composite(force=True).convert('RGBA'));Image.fromarray(array).save(Path(path).with_suffix('.png'));return array
a=decode(obj['exports']['material'],1);b=decode(obj['exports']['object'],2);assert np.max(np.abs(a.astype(int)-b.astype(int)))<=1
c=decode(stochastic['exports'],1)
def oracle(image,report):
 camera=report['camera'];left,right,bottom,top,near,far=camera['frustum'];w,h=480,240
 origin=np.array(camera['origin']);xaxis=np.array(camera['right']);yaxis=np.array(camera['up']);back=np.array(camera['back'])
 sources=[np.array(Image.open(n['path']).convert('RGB')).astype(float) for n in report['native']]
 errors=[]
 def color(source,u,v):
  ih,iw,_=source.shape;px=(u%1)*iw-.5;py=(1-v%1)*ih-.5;ix=int(np.floor(px));iy=int(np.floor(py));tx=px-ix;ty=py-iy
  return np.rint((1-ty)*((1-tx)*source[iy%ih,ix%iw]+tx*source[iy%ih,(ix+1)%iw])+ty*((1-tx)*source[(iy+1)%ih,ix%iw]+tx*source[(iy+1)%ih,(ix+1)%iw]))
 for y in range(3,h-3,5):
  for x in range(3,w-3,5):
   if image[y,x,3]!=255:continue
   samples=[]
   for dy,dx in [(0.25,0.25),(0.25,.75),(.75,.25),(.75,.75)]:
    p=origin+xaxis*(left+(x+dx)/w*(right-left))+yaxis*(top-(y+dy)/h*(top-bottom))-back*near
    owner=0 if 10<p[0]<1990 else 1 if 2510<p[0]<4490 else None
    if owner is None or not 10<p[1]<1990:break
    uv=np.array(report['native'][owner]['uvBasis']);value=uv[0]+p[0]/1000*(uv[1]-uv[0])+p[1]/1000*(uv[2]-uv[0]);samples.append(color(sources[owner],*value))
   if len(samples)==4:errors.append(np.max(np.abs(np.rint(np.mean(samples,axis=0))-image[y,x,:3])))
 assert len(errors)>100 and max(errors)<=2,(len(errors),max(errors,default=999))
 return dict(samples=len(errors),maxError=float(max(errors)))
report=dict(mergedVsObjectEqual=True,objectVariantsMergedIntoOneLayer=True,objectOracle=oracle(a,obj),stochasticOracle=oracle(c,stochastic))
(folder/'psd-verified.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))

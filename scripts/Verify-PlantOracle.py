"""Independent ray/PNG-alpha oracle against native B snapshot and decoded PSD."""
from pathlib import Path
import json,math,numpy as np
from PIL import Image
from psd_tools import PSDImage
root=Path(__file__).resolve().parents[1]/'artifacts/rhino-B/plants015';scene=json.loads((root/'oracle-scene.json').read_text());c=scene['camera'];w,h=scene['width'],scene['height']
origin,right,up,back=[np.array(c[k],float) for k in ['origin','right','up','back']];l,r,b,t,n,f=c['frustum']
norm=lambda x:x/np.linalg.norm(x)
plants=[]
for entry in scene['plants']:
 p=entry['position'];anchor=np.array([p[k] for k in ['x','y','z']]);s=entry['settings'];z=back if c['parallel'] else norm(origin-anchor);flat=np.array([z[0],z[1],0.]);rx=norm(np.cross([0,0,1],flat)) if np.linalg.norm(flat)>1e-9 else right
 angle=math.degrees(math.asin(abs(z[2])));settings=scene['settings'];a=1 if settings['mode']=='free' else 0 if settings['mode']=='z' else np.clip((angle-settings['angle']+settings['transition'])/(2*settings['transition']),0,1);a=a*a*(3-2*a)
 rx=norm(rx*(1-a)+right*a);uy=np.array([0.,0.,1.])*(1-a)+up*a;uy=norm(uy-rx*np.dot(uy,rx));normal=norm(np.cross(rx,uy))
 plants.append(dict(anchor=anchor,right=rx,up=uy,normal=normal,width=s['widthMeters']*s['scale'],height=s['heightMeters']*s['scale'],au=1-s['anchorU'] if s['mirror'] else s['anchorU'],av=s['anchorV'],mirror=s['mirror'],image=np.array(Image.open(s['image']).convert('RGBA'),float)/255))
def sample(im,u,v):
 ih,iw,_=im.shape;x=np.clip(u*iw-.5,0,iw-1);y=np.clip((1-v)*ih-.5,0,ih-1);ix,iy=int(x),int(y);fx,fy=x-ix,y-iy;value=np.zeros(4)
 for j in range(2):
  for i in range(2):
   pix=im[min(iy+j,ih-1),min(ix+i,iw-1)];a=pix[3]*(fx if i else 1-fx)*(fy if j else 1-fy);value[:3]+=pix[:3]*a;value[3]+=a
 return value
def blockers(start,dir):
 distances=[]
 if abs(dir[1])>1e-12:
  d=(-.5-start[1])/dir[1];p=start+dir*d
  if d>=0 and 0<=p[0]<=4 and 0<=p[2]<=2.2:distances.append(d)
 if abs(dir[2])>1e-12:
  d=-start[2]/dir[2];p=start+dir*d
  if d>=0 and -3<=p[0]<=3 and 3<=p[1]<=7:distances.append(d)
 return min(distances,default=math.inf)
def fragment(plant,start,dir):
 den=np.dot(dir,plant['normal'])
 if abs(den)<1e-12:return None
 d=np.dot(plant['anchor']-start,plant['normal'])/den
 if d<0:return None
 p=start+dir*d-plant['anchor'];u=np.dot(p,plant['right'])/plant['width']+plant['au'];v=np.dot(p,plant['up'])/plant['height']+plant['av']
 if not(0<=u<=1 and 0<=v<=1):return None
 return d,sample(plant['image'],1-u if plant['mirror'] else u,v)
def ray(x,y):
 u=x/w;v=1-y/h
 near=origin+right*(l+(r-l)*u)+up*(b+(t-b)*v)-back*n
 far=origin+right*(l+(r-l)*u)*(1 if c['parallel'] else f/n)+up*(b+(t-b)*v)*(1 if c['parallel'] else f/n)-back*f
 return near,norm(far-near),np.linalg.norm(far-near)
def oracle(x,y):
 accum=np.zeros(4)
 for dy,dx in [(.25,.25),(.25,.75),(.75,.25),(.75,.75)]:
  start,dir,length=ray(x+dx,y+dy);blocked=blockers(start,dir);hits=[]
  for p in plants:
   hit=fragment(p,start,dir)
   if hit is not None and hit[0]<=min(length,blocked)+1e-8:hits.append(hit)
  hits.sort(key=lambda h:h[0]);trans=1
  for d,col in hits:accum+=col*trans/4;trans*=1-col[3]
 return np.rint(np.r_[accum[:3]/accum[3] if accum[3]>0 else [0,0,0],accum[3]]*255)
path=next((root/'final-all').glob('*.psd'));psd=PSDImage.open(path);group=next(g for g in psd if g.name=='\u690d\u7269');actual=np.array(group.composite(viewport=psd.viewbox,force=True).convert('RGBA'))
ys,xs=np.nonzero(actual[:,:,3]>0);rng=np.random.default_rng(43);indices=rng.choice(len(xs),min(500,len(xs)),replace=False);errors=[]
for i in indices:
 x,y=int(xs[i]),int(ys[i]);expected=oracle(x,y);errors.append(float(np.max(abs(expected-actual[y,x]))))
assert max(errors)<=2,(max(errors),sorted(errors)[-10:])
off=PSDImage.open(scene['shadowWithout']['files'][0]['path']);off=np.array(next(g for g in off if g.name=='Shadow').composite(viewport=psd.viewbox,force=True).convert('RGBA'))[:,:,3]
on=np.array(next(g for g in psd if g.name=='Shadow').composite(viewport=psd.viewbox,force=True).convert('RGBA'))[:,:,3];delta=on.astype(int)-off.astype(int);assert delta.max()>100 and np.count_nonzero(delta>0)>30
assert delta.min()>=0
report=dict(samples=len(errors),plantPixelMaxError=max(errors),plantShadowsAddedPixels=int(np.count_nonzero(delta>0)),plantShadowsMaxIncrease=int(delta.max()))
(root/'oracle-verified.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))

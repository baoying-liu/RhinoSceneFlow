"""Synthetic scenes and injected defects; never claimed as AI-generated images."""
import sys,uuid,json
from pathlib import Path
import numpy as np,cv2,pyvips
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/RhinoSceneFlow.Plugin/PostProduction'))
import render,project
from fusion_checks import inspect
out=ROOT/'artifacts/final-fusion0223'/uuid.uuid4().hex;out.mkdir(parents=True);rng=np.random.default_rng(23);reports=[]
def preview(p,w,h):return render.array(pyvips.Image.thumbnail(str(p),w,height=h,size='force'))
for name in ['white-model','dense-plants','repeat-texture','4k-reconstruction']:
 w,h=(4096,3072) if name=='4k-reconstruction' else (1200,900);p=out/name;p.mkdir()
 if name=='white-model':
  im=Image.new('RGBA',(w,h),'#eeeeee');d=ImageDraw.Draw(im)
  for x in range(130,1000,260):
   d.rectangle((x,180,x+180,620),fill='#fafafa',outline='#53616a',width=5)
   for xx in range(x+20,x+170,30):d.rectangle((xx,220,xx+16,550),fill='#53747e')
 else:
  texture=rng.integers(70,160,(h,w),dtype=np.uint8);a=np.stack([texture//2,texture,texture//3,np.full_like(texture,255)],axis=2);im=Image.fromarray(a);d=ImageDraw.Draw(im)
  for y in range(40,h,90):
   for x in range(40,w,90):
    if name=='dense-plants':d.ellipse((x,y,x+55,y+70),fill=(60,130,45,180),outline=(20,70,20,230),width=3)
    else:d.rectangle((x,y,x+65,y+40),fill='#ad876a',outline='#d3c6ad',width=3)
 im.save(p/'base.png');mask=np.full((h,w),255,np.uint8);mask[:20,:20]=0;Image.fromarray(mask).save(p/'edit-mask.png');rows=[]
 for t in project.tiles(w,h,2048 if w==4096 else 1024,128):
  file='tile-'+str(t['id'])+'.png';im.convert('RGB').crop(t['context']).save(p/file);rows.append(dict(t,status='completed',image=file))
 state=dict(tiles=rows,fusionId=uuid.uuid4().hex,colorMatch=False);project.write_json(p/'run.json',state);rep=render.compose(p);assert not rep['needsReview'],rep['checks'];assert not rep['checks']['hardFailure']
 base=np.array(im);result=np.array(Image.open(p/rep['image']));assert np.array_equal(base[:,:,3],result[:,:,3]) and np.array_equal(base[:20,:20],result[:20,:20])
 if w==4096:assert result.shape==(3072,4096,4);reports.append(dict(scene=name,coherentFusion=True,checks=rep['checks']));continue
 def check(rgb,name):
  rgba=np.dstack([rgb,base[:,:,3]]);rgba[:20,:20]=base[:20,:20];dest=p/(name+'.png');Image.fromarray(rgba).save(dest);return inspect(p,dest,rows,render.crop,preview)
 rgb=base[:,:,:3].copy();y=rows[0]['core'][3];rgb[y:y+4]=0;bad=check(rgb,'injected-seam');assert bad['review'] and 'seam' in bad['reasons'],bad
 if name!='white-model':
  blur=cv2.GaussianBlur(base[:,:,:3],(0,0),5);badblur=check(blur,'injected-blur');assert 'blur' in badblur['reasons'],badblur
 shifted=cv2.warpAffine(base[:,:,:3],np.float32([[1,0,14],[0,1,0]]),(w,h),borderValue=(255,255,255));double=check(np.minimum(base[:,:,:3],shifted),'injected-double-outline');assert double['review'],double
 broken=base.copy();broken[2,2]=[255,0,255,0];dest=p/'broken-integrity.png';Image.fromarray(broken).save(dest);integrity=inspect(p,dest,rows,render.crop,preview);assert integrity['hardFailure'] and integrity['readonlyChanged'] and integrity['alphaChanged']
 reports.append(dict(scene=name,coherentFusion=True,seamDetected=True,blurDetected=name!='white-model',duplicateOutlineDetected=True,integrityFailureDetected=True))
project.write_json(out/'verified.json',dict(cases=reports,modelCalls=0,folder=str(out)));print(json.dumps(dict(cases=[r['scene'] for r in reports],passed=True,modelCalls=0,folder=str(out))))

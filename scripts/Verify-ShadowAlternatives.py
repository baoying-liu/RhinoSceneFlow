"""Decode research PSDs and explicitly record the CURRENT backend's known accuracy failure."""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from psd_tools import PSDImage
p=Path('artifacts/rhino-B/alternatives')
r=json.loads((p/'contact-counterexample.json').read_text())
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',20)
small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',16)
canvas=Image.new('RGB',(960,410),'white');draw=ImageDraw.Draw(canvas)
for index,c in enumerate(r['cases']):
    im=PSDImage.open(c['export']['path']).topil().convert('RGBA')
    c['actualAlpha']=im.getpixel(tuple(c['probe']))[3]
    background=Image.new('RGBA',im.size,'white');background.alpha_composite(im)
    annotate=ImageDraw.Draw(background)
    annotate.rectangle(c['roofRect'],outline='#2477BD',width=2)
    x,y=c['probe'];annotate.ellipse((x-3,y-3,x+3,y+3),outline='#D53935',width=2)
    crop=background.crop((452,172,612,352)).resize((240,270))
    canvas.paste(crop.convert('RGB'),(index*480+120,58))
    title='平滑顶点法线：阴影消失' if index==0 else '面法线：阴影存在'
    draw.text((index*480+80,18),title,font=font,fill='black')
    draw.text((index*480+115,335),'应为 alpha 255；实际 '+str(c['actualAlpha']),font=small,fill='black')
    background.save(p/('contact-'+c['name']+'-annotated.png'))
draw.text((48,380),'蓝框：上方遮挡片；红点：光线确定被遮挡的接收点。仅顶点法线不同。',font=small,fill='black')
canvas.save(p/'missing-shadow-comparison.png')
r['knownMissingShadowReproduced']=r['cases'][0]['actualAlpha']==0 and r['cases'][1]['actualAlpha']==255
r['currentBackendAccurate']=False
assert r['knownMissingShadowReproduced'],'Previously recorded counterexample changed; re-audit it'
(p/'contact-counterexample-verified.json').write_text(json.dumps(r,indent=2))
native={}
for scheme in ['SceneLighting','None']:
    a=np.asarray(Image.open(p/('native-'+scheme+'-False.png')).convert('RGB')).astype(float)
    b=np.asarray(Image.open(p/('native-'+scheme+'-True.png')).convert('RGB')).astype(float)
    delta=np.maximum(a-b,0).mean(2)
    alpha=np.clip(delta/np.maximum(a.mean(2),1),0,1)
    rgba=np.zeros((*alpha.shape,4),dtype=np.uint8);rgba[:,:,:3]=90;rgba[:,:,3]=np.round(alpha*255)
    im=Image.fromarray(rgba);im.save(p/('native-'+scheme+'-difference.png'))
    white=Image.new('RGBA',im.size,'white');white.alpha_composite(im);white.convert('RGB').save(p/('native-'+scheme+'-difference-white.png'))
    native[scheme]=dict(changedPixelsOver2=int((delta>2).sum()),maxDelta=float(delta.max()),maxAlpha=int(rgba[:,:,3].max()))
base=PSDImage.open(p/'base-colors.psd').topil().convert('RGBA');b=np.asarray(base)
ground=np.all(b==[185,190,195,255],axis=2)
ground=np.asarray(Image.fromarray((ground*255).astype('uint8')).filter(ImageFilter.MinFilter(5)))>0
cur=PSDImage.open(p/'current-False.psd').topil().convert('RGBA')
planar=PSDImage.open(p/'planar-ground.psd').topil().convert('RGBA')
cm=(np.asarray(cur)[:,:,3]>=128)&ground;pm=(np.asarray(planar)[:,:,3]>=128)&ground
union=int((cm|pm).sum());inter=int((cm&pm).sum())
compare=dict(groundPixels=int(ground.sum()),currentPixels=int(cm.sum()),projectedPixels=int(pm.sum()),symmetricDifference=int((cm!=pm).sum()),iou=inter/union)
assert compare['iou']>.99,'Flat-ground agreement changed; re-audit projection'
for name,mask in [('planar-ground',planar),('current',cur)]:
    out=Image.new('RGBA',base.size,'white');out.alpha_composite(base);out.alpha_composite(mask);out.convert('RGB').save(p/(name+'-overlay.png'))
sun=json.loads((p/'verified-sun-45.json').read_text());assert sun['ok'] and sun['renderSettingsRestored']
summary=dict(researchChecksCompleted=True,currentBackendAccurate=False,knownMissingShadowReproduced=True,
    groundComparison=compare,nativeDifferential=native,sunTransactionRetest=sun,
    limitations=['Synthetic contact fixture proves a failure mode; it does not identify every issue in the user scene.',
      'Ground comparison is agreement between mesh methods, not an exact-NURBS truth test.',
      'Native differential retains shadow-map artifacts and is not approved as a clean production mask.',
      'Planar prototype supports a finite flat ground only; no curved receivers.'])
(p/'research-verified.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))

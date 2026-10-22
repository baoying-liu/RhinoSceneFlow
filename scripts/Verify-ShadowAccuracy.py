"""Independent PSD decoding against dense analytic hyperboloid shadow samples."""
import json
from pathlib import Path
import numpy as np
from PIL import Image
from psd_tools import PSDImage
folder=Path('artifacts/rhino-B/accuracy')
report=json.loads((folder/'report.json').read_text())
assert report['version'] in ('0.4.1','0.5.0','0.5.1')
assert report['complete'] and report['viewRestored']
checks=[];failures=[]
for case in report['cases']:
 data=case['result']['export'];psd=PSDImage.open(data['path']);rgba=psd.topil().convert('RGBA');a=np.asarray(rgba)
 assert len(psd)==1 and psd[0].name=='Shadow'
 layer=np.asarray(psd[0].topil().convert('RGBA'));assert np.all(layer[:,:,:3]==90)
 assert set(np.unique(a[:,:,3])).issubset({0,64,128,191,255})
 bad=[];edge=0;positive=0
 for s in case['samples']:
  expected=round(255*sum(s['shadow'])/4);actual=int(a[s['y'],s['x'],3])
  edge+=0<expected<255;positive+=expected>0
  if expected!=actual:bad.append(dict(s,expected=expected,actual=actual))
 assert case['stateUnchanged']
 failures.extend(dict(case=case['name'],**s) for s in bad)
 checks.append(dict(name=case['name'],pixels=len(case['samples']),subsamples=len(case['samples'])*4,boundaryPixels=edge,shadowPixels=positive,failures=len(bad),surfaceQueries=data['surfaceRefinements'],milliseconds=data['elapsedMilliseconds']))
 base=PSDImage.open(case['base']['path']).topil().convert('RGBA');overlay=Image.new('RGBA',base.size,'white');overlay.alpha_composite(base);overlay.alpha_composite(rgba);overlay.save(folder/(case['name']+'-overlay.png'))
 rgba.save(folder/(case['name']+'-shadow.png'))
 if case['name']=='perspective':
  old=PSDImage.open('artifacts/rhino-B/volumes/perspective.psd').topil().convert('RGBA')
  old_overlay=Image.new('RGBA',base.size,'white');old_overlay.alpha_composite(base);old_overlay.alpha_composite(old)
  canvas=Image.new('RGB',(900,650),'white')
  from PIL import ImageDraw
  draw=ImageDraw.Draw(canvas)
  for col,(name,img) in enumerate([('v0.4 mesh volumes',old_overlay),('original-surface refinement',overlay)]):
   crop=img.crop((455,190,550,345)).resize((380,620),Image.Resampling.NEAREST)
   canvas.paste(crop.convert('RGB'),(col*450,30));draw.text((col*450+10,10),name,fill='black')
  canvas.save(folder/'terminator-comparison.png')
mixed=report['mixed'];assert len(mixed)==2
mixed_image=PSDImage.open(folder/'perspective.psd').topil().convert('RGBA')
for sample in mixed:
 expected=round(255*sum(sample['shadow'])/4);actual=mixed_image.getpixel((sample['x'],sample['y']))[3]
 if expected!=actual:failures.append(dict(case='mixed-receiver',**sample,expected=expected,actual=actual))
verified=dict(mixedReceiverPixels=len(mixed),ok=not failures,pid=report['pid'],version=report['version'],checks=checks,failures=failures)
(folder/'verified.json').write_text(json.dumps(verified,indent=2),encoding='utf-8')
print(json.dumps(verified,indent=2))
assert not failures,'Analytic-boundary mismatches retained in verified.json'

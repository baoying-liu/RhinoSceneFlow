from pathlib import Path
from PIL import Image,ImageDraw
import shutil,json,re
ROOT=Path(__file__).resolve().parents[4];F=ROOT/'artifacts/tutorial-full-v01';P=ROOT/'media/tutorial-en/public/case/tutorial-full-v01';P.mkdir(parents=True,exist_ok=True)
# Real screenshots retain their native colours. Crop only; no interface reconstruction.
for src in (F/'captures').glob('*.png'):
 if src.stem=='tools-dropdown':continue
 im=Image.open(src).convert('RGB')
 if im.width<1000:
  direct=F/'direct'/src.name
  if not direct.exists():raise ValueError('Minimized-window capture has no direct WPF replacement: '+src.name)
  # Genuine native panel rendered directly while the owned window is minimized.
  # Reassemble with the earlier unchanged dock shell; the split edit uses only this panel.
  im=Image.open(F/'captures/complete-case.png').convert('RGB');panel=Image.open(direct).convert('RGB');im.paste(panel,(229,271))
 im.resize((1920,1049)).save(P/(src.stem+'-full.jpg'),quality=93)
 for focus,y in [('top',375),('middle',800),('bottom',1290),('lower',1100)]:
  canvas=Image.new('RGB',(690,850),'#19382b')
  header=im.crop((192,271,838,335)).resize((690,68));canvas.paste(header,(0,15))
  body=im.crop((236,y,826,y+690)).resize((630,737));canvas.paste(body,(50,113));canvas.save(P/(src.stem+'-'+focus+'.jpg'),quality=94)
 vp=im.crop((970,650,3320,1950));vp.save(P/(src.stem+'-view.jpg'),quality=95)
for p in F.glob('*.png'):
 if p.stem in ['panel-contact','plant-display-check','tool-menu']:continue
 shutil.copy2(p,P/p.name)
for n in ['orbit.mp4','compare-whole.mp4','compare-local.mp4']:
 if (F/n).exists():shutil.copy2(F/n,P/n)
# Real popup raster captured from native WPF. Its provenance remains in manifest.
if (F/'tool-menu.png').exists():shutil.copy2(F/'tool-menu.png',P/'tool-menu.png')
if (F/'plant-fixed-view.png').exists():
 for name in ['plant-scatter','plant-scatter-start','plant-manual']:
  Image.open(F/'plant-fixed-view.png').convert('RGB').save(P/(name+'-view.jpg'),quality=95)
if (F/'plant-fixed-variation.png').exists():Image.open(F/'plant-fixed-variation.png').convert('RGB').save(P/'plant-scatter-variation-view.jpg',quality=95)
if (F/'plant-corrected-job.json').exists():
 job=json.loads((F/'plant-corrected-job.json').read_text(encoding='utf8'))
 if job.get('status')=='completed':
  a=Path(job['imagePath']);shutil.copy2(a,P/'plant-elevation.png');shutil.copy2(next(a.parent.glob('*summer_plan.png')),P/'plant-plan.png')
text=(F/'basic-captions.md').read_text(encoding='utf8');code=re.search(r'```tsx\n(.*?)\n```',text,re.S).group(1)
(ROOT/'media/tutorial-en/src/basic-captions.element.tsx').write_text(code+'\n',encoding='utf8')
print('Prepared',len(list(P.iterdir())),'assets')

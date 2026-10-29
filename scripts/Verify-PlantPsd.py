"""Independent PSD hierarchy, alpha and compositing checks (not Photoshop UI)."""
from pathlib import Path
import json,numpy as np
from psd_tools import PSDImage
root=Path(__file__).resolve().parents[1]/'artifacts'
report={}
for folder in [root/'validation',root/'rhino-B/plants015']:
 items={}
 for mode in ['individual','species','all']:
  path=folder/('plants-'+mode+'.psd') if folder.name=='validation' else next((folder/mode).glob('*.psd'))
  psd=PSDImage.open(path);group=next(g for g in psd if g.name=='\u690d\u7269');assert group.is_group()
  layers=list(group.descendants());pixels=[l for l in layers if not l.is_group()]
  if mode=='individual':
   sub=[l for l in group if l.is_group()];assert len(sub)==2
   assert all(' ' in l.name for l in sub)
  if mode=='species':assert len(pixels)==2 and all(' ' in p.name for p in pixels)
  if mode=='all':assert len(pixels)==1
  image=group.composite(viewport=psd.viewbox,force=True);assert image is not None
  image.save(folder/('decoded-plants-'+mode+'.png'));items[mode]=np.array(image.convert('RGBA'))
  assert (items[mode][:,:,3]==0).any() and (items[mode][:,:,3]>0).any()
  if folder.name!='validation':assert list(psd)[-1].name=='\u690d\u7269' # psd-tools iterates bottom to top.
 a,b=items['species'].astype(int),items['all'].astype(int)
 mask=(a[:,:,3]>0)|(b[:,:,3]>0);diff=np.max(abs(a[mask]-b[mask]));assert diff<=2,diff
 report[str(folder.relative_to(root))]=dict(hierarchy=True,realTransparency=True,speciesVsAllMaxError=int(diff),individualPixelsIndependent=bool(np.any(items['individual']!=items['species'])))
 # Source model requires independent mode to retain overlap that merging clips.
 assert report[str(folder.relative_to(root))]['individualPixelsIndependent']
(root/'rhino-B/plants015/psd-verified.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))

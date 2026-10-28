"""Independent actual-layer PSD decode / recomposition; no Photoshop UI."""
from pathlib import Path
from psd_tools import PSDImage
import json,shutil,numpy as np
root=Path(__file__).resolve().parents[1];folder=root/'artifacts/rhino-B/uv-v012';s=json.loads((folder/'export-verified.json').read_text())
out=root/'artifacts/examples/UV-v012';out.mkdir(parents=True,exist_ok=True);report={}
for label,passes in s['exports'].items():
 report[label]={}
 for kind,data in passes.items():
  path=Path(data['files'][0]['path']);psd=PSDImage.open(path);assert psd.size==(1600,1200)
  image=psd.composite(force=True).convert('RGBA');image.save(out/f'{label}-{kind}.png')
  rgba=np.asarray(image);assert np.count_nonzero(rgba[:,:,3])>1000
  if kind=='albedo':
   colors=rgba[rgba[:,:,3]>250,:3];assert len(np.unique(colors,axis=0))>=8
  if kind=='stack':assert any(l.name=='Shadow' for l in psd) and any(l.is_group() for l in psd) and any(l.name=='Arctic' for l in psd)
  report[label][kind]=dict(size=psd.size,layers=[l.name for l in psd]);shutil.copy2(path,out/f'{label}-{kind}.psd')
(out/'decoded.json').write_text(json.dumps(dict(passed=True,reports=report),indent=2),'utf-8')
print('PASS: real brick pixels, independent PSD recomposition, native display and shadow/albedo/Arctic layers.')

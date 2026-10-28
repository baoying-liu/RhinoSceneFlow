"""Independent PSD/image verification; no Rhino or Photoshop UI."""
import json,hashlib,shutil
from pathlib import Path
import numpy as np
from PIL import Image
from psd_tools import PSDImage
root=Path(__file__).resolve().parents[1];folder=root/'artifacts/rhino-B/workspace013';receipt=json.loads((folder/'export-verified.json').read_text())
path=Path(receipt['paths'][0]);psd=PSDImage.open(path);assert psd.size==(320,240)
for file in receipt['paths']:
 decoded=PSDImage.open(file);assert decoded.size==(320,240)
 assert [l.name for l in decoded]==['Arctic','材质','Shadow']
 decoded.composite(force=True)
layers=list(psd);shadow=layers[-1];assert shadow.name=='Shadow' and shadow.opacity==191,layers
group=next(l for l in layers if l.is_group());assert len(list(group))>=2
rgb=np.array(group.composite().convert('RGBA'));blue=(rgb[:,:,2]>rgb[:,:,0]*1.3)&(rgb[:,:,3]>0);assert blue.sum()>100,int(blue.sum())
mask=np.array(shadow.topil().convert('RGBA'));assert mask[:,:,3].max()>0
assert any('Arctic' in l.name for l in layers)
full=psd.composite(force=True);full.save(folder/'psd-composite.png')
asset=json.loads((folder/'generation-verified.json').read_text())['asset'];imagePath=folder/'library/assets'/asset['id'].replace('-','')/asset['maps']['baseColor'];assert hashlib.sha256(imagePath.read_bytes()).hexdigest().upper()==asset['sha256']['baseColor'];Image.open(imagePath).verify()
out=root/'artifacts/examples/Workspace013';out.mkdir(parents=True,exist_ok=True);shutil.copy2(path,out/'SceneFlow-Workspace.psd');shutil.copy2(folder/'psd-composite.png',out/'SceneFlow-Workspace.png');shutil.copy2(folder/'sphere-native.png',out/'sphere-native.png')
report=dict(passed=True,files=len(receipt['paths']),independentDecoder='psd-tools',photoshopUi=False,layers=[l.name for l in layers],materialChildren=len(list(group)),bluePixels=int(blue.sum()),shadowPresent=True,freshImageChecksum=True)
(folder/'decoded.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))

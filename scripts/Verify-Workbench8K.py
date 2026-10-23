"""Independently decode every pixel layer and merged image from the real B 8K export."""
import json
from pathlib import Path
from psd_tools import PSDImage
root=Path(__file__).resolve().parents[1];folder=root/'artifacts/rhino-B/workbench'
report=json.loads((folder/'8k-report.json').read_text())
file=Path(report['result']['files'][0]['path']);psd=PSDImage.open(file)
assert report['ok'] and report['stateUnchanged'] and psd.size==(8192,2048)
assert len(psd)==1 and psd[0].is_group() and len(psd[0])>=6
for layer in psd[0]:
 image=layer.topil().convert('RGBA');assert image.size==(layer.width,layer.height)
 assert image.getchannel('A').getbbox() is not None
merged=psd.topil().convert('RGBA');assert merged.getchannel('A').getbbox() is not None
merged.thumbnail((1024,1024));merged.save(folder/'8k-preview.png')
result=dict(ok=True,pid=report['pid'],size=psd.size,bytes=file.stat().st_size,layers=len(psd[0]),allLayersDecoded=True)
(folder/'8k-verified.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))

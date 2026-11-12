"""Read existing demonstration exports; never modify the original PSD/model."""
from pathlib import Path
import hashlib,json,shutil
from psd_tools import PSDImage
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent/'public/case'
OUT.mkdir(parents=True,exist_ok=True)
sources={
 'before.png':'artifacts/examples/PostProduction-v019/Hillside-Original.png',
 'after.png':'artifacts/examples/PostProduction-v019/Hillside-AI-Result.png',
}
manifest=[]
for name,source in sources.items():
 p=ROOT/source
 shutil.copyfile(p,OUT/name)
 manifest.append(dict(file=name,source=source,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
source='artifacts/psd-guides-02214/hillside-six-channels.psd'
p=ROOT/source
before=hashlib.sha256(p.read_bytes()).hexdigest()
psd=PSDImage.open(p)
for layer,name in zip(psd,['colors','depth','arctic','textures','shadow','plants']):
 layer.visible=True
 im=layer.composite(force=True)
 canvas=Image.new('RGBA',psd.size)
 if im is not None: canvas.paste(im,(layer.left,layer.top))
 canvas.save(OUT/(name+'.png'))
 manifest.append(dict(file=name+'.png',source=source,sourceLayer=layer.name,sourceSha256=before))
assert hashlib.sha256(p.read_bytes()).hexdigest()==before
(OUT/'provenance.json').write_text(json.dumps(dict(status='previous actual test exports; not new screen recordings',assets=manifest),indent=2),encoding='utf8')
print('Prepared eight case assets; source PSD unchanged.')

"""Independent psd-tools decode/recomposition of the actual ChatKit/xatlas workflow exports."""
from pathlib import Path
from psd_tools import PSDImage
from psd_tools.constants import BlendMode
import json,numpy as np
root=Path(__file__).resolve().parents[1];r=root/'artifacts/examples/ChatKit-Xatlas'
a=PSDImage.open(r/'AI_Complex_Merged.psd');b=PSDImage.open(r/'AI_Complex_ByObject.psd')
def summary(p):return [dict(name=l.name,kind=l.kind,blend=str(l.blend_mode),opacity=l.opacity,children=[x.name for x in l] if l.is_group() else []) for l in p]
def rgba(image):
 x=np.asarray(image.convert('RGBA')).astype(float);x[:,:,:3]*=x[:,:,3:4]/255;return x
assert a.size==b.size==(1024,768)
for p,count in [(a,1),(b,2)]:
 group=next(l for l in p if l.is_group());assert len(group)==count and all(not x.is_group() for x in group)
 shadow=next(l for l in p if l.name=='Shadow');assert shadow.blend_mode==BlendMode.MULTIPLY and shadow.opacity==191
 assert any(l.name=='Arctic' for l in p)
first=a.composite(force=True);second=b.composite(force=True);error=float(np.abs(rgba(first)-rgba(second)).max());assert error<=2,error
previewError=float(np.abs(rgba(first)-rgba(a.composite())).max());assert previewError<=2,previewError
first.save(r/'preview.png');second.save(r/'preview-by-object.png')
texture=next(l for l in a if l.is_group())[0].topil().convert('RGBA');colors=np.asarray(texture);assert len(np.unique(colors[colors[:,:,3]>250,:3],axis=0))>8
report=dict(size=a.size,compositeDifference=error,storedPreviewDifference=previewError,merged=summary(a),byObject=summary(b),passed=True)
(r/'decoded.json').write_text(json.dumps(report,indent=2),'utf-8');print(json.dumps(report,ensure_ascii=True))

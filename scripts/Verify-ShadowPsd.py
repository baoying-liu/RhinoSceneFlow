"""Independent PSD decoding: exact-Brep oracle, uniform RGB, alpha, alignment and recomposition."""
import json
from pathlib import Path
import numpy as np
from PIL import Image
from psd_tools import PSDImage
folder=Path('artifacts/rhino-B/shadows')
report=json.loads((folder/'report.json').read_text())
assert report['complete']
command=PSDImage.open(report['commandPath']);assert command.width==128 and len(command)==1
assert report['sun']['identical']
style=PSDImage.open(report['style']['export']['path'])[0].topil().convert('RGBA')
sp=np.asarray(style);assert np.all(sp[:,:,:3]==[18,52,86]) and sp[:,:,3].max()==128
default=PSDImage.open(report['defaultResolution']['export']['path'])
assert default.width==2048 and len(default)==1
full=default[0].topil().convert('RGBA');fp=np.asarray(full)
assert np.all(fp[:,:,:3]==90) and fp[:,:,3].max()==255
full_image=default.topil().convert('RGBA');full_image.save(folder/'default-2048-shadow.png')
checks=[]
for case in report['cases']:
    data=case['result'];exp=data['export'];psd=PSDImage.open(exp['path'])
    assert len(psd)==1 and psd[0].name=='Shadow'
    assert psd.size==(exp['width'],exp['height'])
    layer=psd[0].topil().convert('RGBA');pixels=np.asarray(layer)
    assert np.all(pixels[:,:,:3]==90),'Shadow RGB must be uniform, including antialiased edges'
    assert set(np.unique(pixels[:,:,3])).issubset({0,64,128,191,255}),'Only 2x2 edge coverage may vary alpha'
    merged=psd.topil().convert('RGBA');a=np.asarray(merged)
    composed=psd.composite(force=True).convert('RGBA')
    def premul(im):
        p=np.asarray(im).astype(float);p[:,:,:3]*=p[:,:,3:]/255;return p
    error=float(np.abs(premul(merged)-premul(composed)).max());assert error<=3,error
    fails=[];receivers={};positive=0
    for s in case['samples']:
        alpha=merged.getpixel((s['x'],s['y']))[3]
        if alpha!=(255 if s['shadow'] else 0):fails.append(dict(s,alpha=alpha))
        if s['shadow']:positive+=1;receivers[s['receiver']]=receivers.get(s['receiver'],0)+1
    assert not fails,(case['name'],len(fails),fails[:12])
    assert positive>0
    assert case['stateUnchanged']
    merged.save(folder/(case['name']+'-shadow.png'))
    base=PSDImage.open(case['base']['path']).topil().convert('RGBA');assert base.size==merged.size
    backdrop=Image.new('RGBA',base.size,'white');backdrop.alpha_composite(base);backdrop.alpha_composite(merged)
    backdrop.convert('RGB').save(folder/(case['name']+'-overlay.png'))
    checks.append(dict(name=case['name'],samples=len(case['samples']),shadowSamples=positive,receivers=receivers,
        triangles=exp['triangles'],milliseconds=exp['elapsedMilliseconds'],maxRecomposeError=error))
# Core fixtures verify non-default opacity and a valid fully transparent shadow layer.
for name,value in [('shadow',255),('shadow-opacity',128)]:
    p=PSDImage.open('artifacts/validation/'+name+'.psd');assert p.topil().convert('RGBA').getpixel((30,50))[3]==value
p=PSDImage.open('artifacts/validation/shadow-empty.psd');assert len(p)==1 and np.asarray(p.topil().convert('RGBA'))[:,:,3].max()==0
verified=dict(ok=True,pid=report['pid'],version=report['version'],checks=checks,defaultResolution=report['defaultResolution']['export'])
(folder/'verified.json').write_text(json.dumps(verified,indent=2),encoding='utf-8')
print(json.dumps(verified,indent=2))

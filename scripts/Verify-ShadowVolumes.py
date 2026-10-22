"""Independent psd-tools verification for volume exports and exact-Brep samples."""
import json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from psd_tools import PSDImage
folder=Path('artifacts/rhino-B/volumes-v041')
report=json.loads((folder/'report.json').read_text())
assert report['version']=='0.4.1'
assert report['complete'] and report['viewRestored'] and report['invalidBackendRejected']
command=PSDImage.open(report['commandPath']);assert command.width==128 and len(command)==1
style=PSDImage.open(report['style']['export']['path'])[0].topil().convert('RGBA')
sp=np.asarray(style);assert np.all(sp[:,:,:3]==[18,52,86]) and sp[:,:,3].max()==128
full=PSDImage.open(report['defaultResolution']['export']['path']);assert full.width==2048
full.topil().save(folder/'default-2048-shadow.png')
all_fails=[]
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
    all_fails.extend(dict(case=case['name'],**f) for f in fails)
    assert positive>0
    assert case['stateUnchanged']
    merged.save(folder/(case['name']+'-shadow.png'))
    base=PSDImage.open(case['base']['path']).topil().convert('RGBA');assert base.size==merged.size
    backdrop=Image.new('RGBA',base.size,'white');backdrop.alpha_composite(base);backdrop.alpha_composite(merged)
    backdrop.convert('RGB').save(folder/(case['name']+'-overlay.png'))
    checks.append(dict(name=case['name'],samples=len(case['samples']),shadowSamples=positive,receivers=receivers,
        triangles=exp['triangles'],milliseconds=exp['elapsedMilliseconds'],maxRecomposeError=error,failures=len(fails)))

gaps=[]
canvas=Image.new('RGB',(1024,620),'white');draw=ImageDraw.Draw(canvas)
for row,case in enumerate(report['gap']):
    for col,backend in enumerate(['ray','volume']):
        psd=PSDImage.open(case[backend]['export']['path']);im=psd.topil().convert('RGBA')
        alpha=im.getpixel(tuple(case['probe']))[3]
        expected=0 if backend=='ray' and case['name']=='smooth-receiver' else 255
        assert alpha==expected,(case['name'],backend,alpha)
        gaps.append(dict(name=case['name'],backend=backend,alpha=alpha))
        tile=Image.new('RGBA',im.size,'white');tile.alpha_composite(im);tile=tile.convert('RGB');tile.thumbnail((500,265))
        canvas.paste(tile,(col*512,row*310+35));draw.text((col*512+10,row*310+10),case['name']+' / '+backend+' / center alpha='+str(alpha),fill='black')
canvas.save(folder/'gap-comparison.png')
mesh_a=np.asarray(PSDImage.open(folder/'perspective.psd').topil().convert('RGBA'))[:,:,3]
mesh_b=np.asarray(PSDImage.open(folder/'geometric-ray-perspective.psd').topil().convert('RGBA'))[:,:,3]
mesh_delta=np.abs(mesh_a.astype(int)-mesh_b.astype(int))
mesh_comparison=dict(differentPixels=int(np.count_nonzero(mesh_delta)),maxAlphaDifference=int(mesh_delta.max()))
# Original-surface refinement intentionally differs from the faceted ray reference.
mesh_comparison['expectedToDifferFromMesh']=True
assert report['sun']['samePsdBytes'] and report['sun']['settingsRestored']
verified=dict(meshComparison=mesh_comparison,ok=not all_fails,pid=report['pid'],version=report['version'],checks=checks,gaps=gaps,failures=all_fails,defaultResolution=report['defaultResolution']['export'])
(folder/'verified.json').write_text(json.dumps(verified,indent=2),encoding='utf-8')
print(json.dumps(verified,indent=2))
assert not all_fails,'Exact-Brep oracle mismatch; retained verified.json and previews'

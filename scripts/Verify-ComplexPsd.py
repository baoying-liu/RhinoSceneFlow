"""Compare exported PSDs to Rhino exact-Brep ray oracle and analytical sphere coverage."""
import json,math
from pathlib import Path
import numpy as np
from psd_tools import PSDImage

folder=Path('artifacts/rhino-B/complex')
report=json.loads((folder/'report.json').read_text())
assert report.get('complete'),'Rhino test did not finish'
checks=[]
for case in report['cases']:
    psd=PSDImage.open(case['export']['path']); merged=psd.topil().convert('RGBA')
    assert psd.size==(case['export']['width'],case['export']['height'])
    assert len(psd)==6,[(l.name,l.bbox) for l in psd]
    failures=[];counts={}
    for sample in case['samples']:
        name=sample['expected'];pixel=merged.getpixel((sample['x'],sample['y']))
        counts[name or 'background']=counts.get(name or 'background',0)+1
        expected=tuple(report['colors'][name]+[255]) if name else (0,0,0,0)
        if (pixel!=expected if name else pixel[3]!=0):failures.append(dict(sample,pixel=pixel,expectedRGBA=expected))
    assert not failures,(case['name'],len(failures),failures[:8])
    def premul(image):
        a=np.asarray(image).astype(float);a[:,:,:3]*=a[:,:,3:]/255;return a
    difference=float(np.abs(premul(psd.composite(force=True).convert('RGBA'))-premul(merged)).max())
    assert difference<=3,difference
    for hole in case.get('holes',[]):
        assert merged.getpixel((hole['x'],hole['y']))==tuple(report['colors']['Ground']+[255]),hole
    check={'view':case['name'],'layers':len(psd),'triangles':case['export']['triangles'],
        'milliseconds':case['export']['elapsedMilliseconds'],'nativeRayChecks':counts,
        'maxCompositeError':difference}
    if 'sphereCircle' in case:
        circle=case['sphereCircle'];radius=circle['radius']
        x0=int(math.floor(circle['x']-radius-2));x1=int(math.ceil(circle['x']+radius+2))
        y0=int(math.floor(circle['y']-radius-2));y1=int(math.ceil(circle['y']+radius+2))
        # Layer alpha is conditional on layers above, not geometric coverage. Recover true
        # supersample coverage from merged blue against the known gray ground behind the sphere.
        pixels=np.asarray(merged)[y0:y1,x0:x1,2].astype(float)
        coverage=np.clip((report['colors']['Ground'][2]-pixels)/
            (report['colors']['Ground'][2]-report['colors']['Sphere'][2]),0,1)
        area=float(coverage.sum());ideal=math.pi*radius**2
        error=abs(area-ideal)/ideal
        assert error<.02,('Sphere silhouette area differs by more than 2%',error)
        check['sphereAreaErrorPercent']=100*error
    merged.save(folder/(case['name']+'-psd.png'));checks.append(check)
verified={'ok':True,'pid':report['pid'],'objects':report['objects'],'checks':checks}
(folder/'verified.json').write_text(json.dumps(verified,indent=2),encoding='utf-8')
print(json.dumps(verified,indent=2))

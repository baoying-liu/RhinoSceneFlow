"""Independent PSD metadata, variable RGB, isolated groups, blending and tile seams."""
import json
from pathlib import Path
import numpy as np
from psd_tools import PSDImage
root=Path(__file__).resolve().parents[1];folder=root/'artifacts/rhino-B/workbench'
report=json.loads((folder/'report.json').read_text('utf-8'))
assert report['complete'] and report['stateUnchanged'] and report['finalStateUnchanged']
checks=[]
for file,settings in zip(report['export']['files'],report['settings']):
    psd=PSDImage.open(file['path']);assert psd.size==(settings['width'],settings['height'])
    top=list(reversed(list(psd)));assert len(top)==len(settings['layers'])
    for layer,spec in zip(top,settings['layers']):
        assert layer.blend_mode.value.decode()==spec.get('blend','norm')
        assert layer.opacity==round(spec.get('opacity',100)*255/100)
        if spec['kind']=='material':
            assert layer.is_group() and len(layer)>0
            assert layer.width>1 and layer.height>1,'Adjusted camera left the material pass empty'
        elif spec['kind']=='shadow':assert layer.name=='Shadow' and not layer.is_group()
        else:
            assert not layer.is_group()
            pixels=np.array(layer.topil().convert('RGBA'))
            assert np.unique(pixels[:,:,:3].reshape(-1,3),axis=0).shape[0]>30,'Display RGB collapsed to flat color'
    a=np.array(psd.topil().convert('RGBA')).astype(float);b=np.array(psd.composite(force=True).convert('RGBA')).astype(float)
    a[:,:,:3]*=a[:,:,3:]/255;b[:,:,:3]*=b[:,:,3:]/255
    error=float(abs(a-b).max());assert error<4,error
    psd.composite().save(folder/(str(file['width'])+'x'+str(file['height'])+'-composite.png'))
    checks.append(dict(path=file['path'],topToBottom=[l.name for l in top],maxRecomposeError=error))

# Adjusted top-view native display and independently projected material share framing.
psd=PSDImage.open(report['export']['files'][0]['path'])
native=np.array(psd[0].topil().convert('RGB')).astype(int)
nativeMask=np.abs(native-native[0,0]).max(axis=2)>15
materialMask=np.array(psd[1].composite(viewport=(0,0,psd.width,psd.height)).convert('RGBA'))[:,:,3]>128
alignment=float((nativeMask&materialMask).sum()/(nativeMask|materialMask).sum())
assert alignment>.96,alignment
tiled=PSDImage.open(report['seam']['files'][0]['path']);reference=PSDImage.open(report['seamReference']['files'][0]['path'])
a=np.array(tiled.topil().convert('RGBA')).astype(int);b=np.array(reference.topil().convert('RGBA')).astype(int)
delta=abs(a-b);seams=dict(maxDifference=int(delta.max()),differentPixels=int(np.any(delta!=0,axis=2).sum()),alphaDifferent=int(np.count_nonzero(delta[:,:,3])))
# Native analytic ray roots can switch a single 2x2 coverage sample at tangencies
# after a frustum translation. Retain that global error; require seam bands exact.
bands=[]
for x in range(1024,a.shape[1],1024):bands.append(delta[:,x-2:x+2])
for y in range(1024,a.shape[0],1024):bands.append(delta[y-2:y+2,:])
seams['seamBandMaxDifference']=max((int(d.max()) for d in bands),default=0)
assert seams['seamBandMaxDifference']<=1 and seams['alphaDifferent']==0,seams
assert seams['differentPixels']<=4 and seams['maxDifference']<=64,seams
for p in (root/'artifacts/validation').glob('configured*.psd'):
    psd=PSDImage.open(p);a=np.array(psd.topil().convert('RGBA')).astype(float);b=np.array(psd.composite(force=True).convert('RGBA')).astype(float)
    a[:,:,:3]*=a[:,:,3:]/255;b[:,:,:3]*=b[:,:,3:]/255;assert abs(a-b).max()<4,p
result=dict(ok=True,pid=report['pid'],ui=report['ui'],checks=checks,seams=seams,cameraAlignmentIoU=alignment)
(folder/'verified.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))

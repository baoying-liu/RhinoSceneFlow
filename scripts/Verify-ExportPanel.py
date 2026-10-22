"""Independent PSD decoding for per-view batch dimensions, channels and recomposition."""
import json
from pathlib import Path
import numpy as np
from PIL import Image
from psd_tools import PSDImage
folder=Path('artifacts/rhino-B/panel')
report=json.loads((folder/'report.json').read_text(encoding='utf-8'))
assert report['complete'] and report['stateUnchanged'] and report['version']=='0.5.0'
checks=[]
def verify(result,channels,label):
    for f in result['files']:
        assert f['ok'],f
        psd=PSDImage.open(f['path']);assert psd.size==(f['width'],f['height']) and len(psd)==f['layers']
        names=[layer.name for layer in psd]
        assert ('Shadow' in names)==('shadow' in channels),(label,names)
        if channels==['shadow']:assert names==['Shadow']
        if 'material' in channels:assert any(n!='Shadow' for n in names)
        if 'Shadow' in names:
            shadow=next(l for l in psd if l.name=='Shadow')
            a=np.asarray(shadow.topil().convert('RGBA'));assert np.all(a[:,:,:3]==90)
        rgba=psd.topil().convert('RGBA');merged=np.asarray(rgba).astype(float)
        recomposed=np.asarray(psd.composite(force=True).convert('RGBA')).astype(float)
        merged[:,:,:3]*=merged[:,:,3:]/255;recomposed[:,:,:3]*=recomposed[:,:,3:]/255
        error=float(abs(merged-recomposed).max());assert error<4,(label,error)
        rgba.save(folder/(label+'-'+str(f['width'])+'x'+str(f['height'])+'.png'))
        checks.append(dict(name=f['name'],width=f['width'],height=f['height'],layers=names,path=f['path'],maxRecomposeError=error))
verify(report['combined'],['material','shadow'],'combined')
for i,c in enumerate(report['cases']):verify(c['result'],c['channels'],'channel-'+str(i))
verify(report['numbered'],['material'],'numbered');verify(report['overwrite'],['material'],'overwrite')
assert Path(report['numbered']['files'][0]['path']).stem.endswith('003')
assert len({(f['width'],f['height']) for f in report['combined']['files']})==3
both=PSDImage.open(report['combined']['files'][0]['path'])
material_file=next(c for c in report['cases'] if c['channels']==['material'])['result']['files'][0]['path']
shadow_file=next(c for c in report['cases'] if c['channels']==['shadow'])['result']['files'][0]['path']
material_only=PSDImage.open(material_file)
a=np.asarray(both.composite(force=True,layer_filter=lambda l:l.name!='Shadow').convert('RGBA'))
b=np.asarray(material_only.composite(force=True).convert('RGBA'))
assert np.array_equal(a,b),'Material channel changed when shadow was selected'
combined_shadow=next(l for l in both if l.name=='Shadow');single_shadow=PSDImage.open(shadow_file)[0]
assert combined_shadow.bbox==single_shadow.bbox and np.array_equal(np.asarray(combined_shadow.topil()),np.asarray(single_shadow.topil()))
ui=report['ui'];assert ui['dimensionsPreserved'] and ui['stateUnchanged']
hashes=[]
for p in ui['previews']:
    image=Image.open(p['path']).convert('RGB');a=np.asarray(image)
    assert image.width>=64 and image.height>=64 and np.std(a)>15,'Blank native preview'
    hashes.append(hash(a.tobytes()))
assert len(set(hashes))>=2,'Display modes did not change the preview'
verified=dict(channelsAligned=True,ok=True,pid=report['pid'],checks=checks,nativePreviewModes=[p['mode'] for p in ui['previews']])
(folder/'verified.json').write_text(json.dumps(verified,indent=2),encoding='utf-8')
print(json.dumps(verified,indent=2))

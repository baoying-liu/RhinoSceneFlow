"""Independent PSD decoding and real raster-worker emission guide preparation; no AI image calls."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
from PIL import Image
from psd_tools import PSDImage
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src/RhinoSceneFlow.Plugin/PostProduction'))
import project,board_render,psd_guides
from board_store import params
out=ROOT/'artifacts/emission/guides';out.mkdir(parents=True,exist_ok=True)
for mode in ('merged','separated'):
    source=ROOT/f'artifacts/validation/emission-{mode}.psd';psd=PSDImage.open(source)
    assert psd[0].blend_mode.value==b'hLit'
    assert psd[0].is_group()==(mode=='separated')
    folder=out/mode;folder.mkdir(exist_ok=True);(folder/'source.psd').write_bytes(source.read_bytes())
    digest=hashlib.sha256(source.read_bytes()).hexdigest();project.prepare(folder)
    doc=project.read_json(folder/'document.json');rows=doc['layers']
    settings=psd_guides.settings(rows,{})
    assert all(r['guideKind']=='emission' and r['role']=='reference' for r in settings)
    manifest=psd_guides.prepare(folder,folder/'source.psd',settings)
    assert len(manifest)==1 and manifest[0]['kind']=='emission'
    assert np.asarray(Image.open(folder/'psd-guides.png')).std()>10
    assert not psd_guides.prepare(folder,folder/'source.psd',psd_guides.settings(rows,{'layerParticipation':{rows[0]['id']:False}}))
    assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
    check=folder/'preflight';check.mkdir(exist_ok=True)
    w,h=psd.size
    snapshot=dict(image=str(folder/'composite.png'),psd=str(folder/'source.psd'),layers=rows,references=[],node=dict(params=params(dict(prompt='Night scene: preserve emitter placement and add local light spill.',edgeGuard=0)),pose=dict(x=0,y=0,width=w,height=h),frame=dict(x=0,y=0,width=w,height=h),annotations=[]))
    project.write_json(check/'snapshot.json',snapshot);board_render.prepare(check)
    prepared=project.read_json(check/'prepared.json');assert prepared['guides'][0]['kind']=='emission'
    assert np.array_equal(np.asarray(Image.open(check/'base.png')),np.asarray(Image.open(folder/'composite.png'))),'Canonical pixels changed'
    print('PASS:',mode,'PSD Hard Light, hierarchy, real emission guide pixels, participation-off and source integrity')

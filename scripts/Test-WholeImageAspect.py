"""Real raster worker, synthetic identity/edge oracles; no model calls."""
from pathlib import Path
import json,sys,uuid
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src/RhinoSceneFlow.Plugin/PostProduction'))
from board_store import Store
from board_render import prepare,finish
out=ROOT/'artifacts/whole-aspect'/uuid.uuid4().hex;out.mkdir(parents=True)
store=Store(out);b=store.create('Whole-image aspect regression');bid=b['id']
for width,height in [(320,180),(180,320),(256,256)]:
    folder=out/f'{width}x{height}';folder.mkdir()
    y,x=np.indices((height,width));rgb=np.stack([x%200+20,y%200+20,(x+y)%200+20],axis=2).astype('uint8')
    # Edge markers make cropping, stretching and newly introduced padding visible.
    rgb[0,:]=[230,25,30];rgb[-1,:]=[25,230,30];rgb[:,0]=[25,30,230];rgb[:,-1]=[220,210,20]
    image=folder/'source.png';Image.fromarray(rgb).save(image)
    asset=store.put_asset(bid,image);source=store.append(bid,asset,asset,width,height,'source.png');node=store.branch(bid,source['id'])
    (folder/'snapshot.json').write_text(json.dumps(dict(node=node,image=str(image),references=[])))
    prepare(folder);p=json.loads((folder/'prepared.json').read_text())
    assert p['inputLayout']=='native-aspect-v1'
    with Image.open(folder/'input.png') as native:assert native.size==(width,height);native.save(folder/'generated.png')
    with Image.open(folder/'editable.png') as mask:assert mask.size==(width,height)
    finish(folder);result=np.array(Image.open(folder/'result.png'))
    assert np.array_equal(result[:,:,:3],rgb),'Identity generation changed edge/content pixels'
    assert np.all(result[:,:,3]==255)
    if width!=height:
        (folder/'result.png').unlink();Image.new('RGB',(256,256),'white').save(folder/'generated.png')
        try:finish(folder)
        except ValueError as error:assert 'aspect ratio' in str(error)
        else:raise AssertionError('Mismatched output must not be stretched/cropped into publication')
        assert not (folder/'result.png').exists()
legacy=out/'legacy';legacy.mkdir();image=legacy/'base.png';Image.new('RGBA',(320,180),'#a97853').save(image)
Image.new('L',(320,180),255).save(legacy/'mask.png');Image.new('RGB',(1024,1024),'#6e9274').save(legacy/'generated.png')
(legacy/'snapshot.json').write_text('{}');(legacy/'prepared.json').write_text(json.dumps(dict(offset=[0,336],size=[1536,864],editablePixels=320*180,totalPixels=320*180)))
finish(legacy);assert Image.open(legacy/'result.png').size==(320,180)
print(json.dumps(dict(nativeLandscapePortraitSquare=True,edgePixelsExact=True,wrongAspectRejected=True,legacyFrozenTask=True,modelCalls=0,folder=str(out))))

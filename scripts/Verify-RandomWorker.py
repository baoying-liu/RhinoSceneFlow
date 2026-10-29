"""Independent image decode of the real texture worker, with source and result fixtures."""
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,json,hashlib,subprocess
root=Path(__file__).resolve().parents[1];folder=root/'artifacts/random-worker';folder.mkdir(exist_ok=True)
worker=root/'src/RhinoSceneFlow.TextureWorker/bin/Release/net8.0-windows/SceneFlow.TextureWorker.exe'
rng=np.random.default_rng(31);pixels=np.clip(rng.normal(145,18,(128,128,3)),0,255).astype('uint8');natural=Image.fromarray(pixels)
d=ImageDraw.Draw(natural);d.ellipse((10,15,35,40),fill=(80,85,65));d.ellipse((77,83,94,100),fill=(180,165,120));natural.save(folder/'natural.png')
brick=Image.new('RGB',(128,128),(190,90,55));d=ImageDraw.Draw(brick)
for row in range(4):
 y=row*32;d.rectangle((0,y,127,y+2),fill=(210,210,200))
 for col in range(-1,5):
  x=col*32+(row%2)*16;d.rectangle((x,y,x+2,y+31),fill=(210,210,200))
brick.save(folder/'brick.png');Image.new('RGB',(128,128),(220,128,220)).save(folder/'normal.png');Image.new('RGB',(64,64),(140,140,140)).save(folder/'roughness.png')
reports=[]
for mode in ['object','stochastic','macro','structured']:
 source='brick' if mode=='structured' else 'natural';maps={s:str(folder/(name+'.png')) for s,name in [('baseColor',source),('normal','normal'),('roughness','roughness')]}
 settings=dict(mode=mode,seed=42,strength=.15,tiles=4,rotate=True,columns=4,rows=4,rowOffset=.5)
 key=hashlib.sha256(json.dumps(dict(contract='uv-up-1',maps=maps,settings=settings)).encode()).hexdigest().upper();target=folder/key
 request=dict(version=1,key=key,maps=maps,sha256={s:hashlib.sha256(Path(p).read_bytes()).hexdigest().upper() for s,p in maps.items()},settings=settings,seed=123,widthMeters=2,heightMeters=1,outputDirectory=str(target))
 path=folder/(mode+'.json');path.write_text(json.dumps(request));run=subprocess.run([str(worker),str(path)],capture_output=True,text=True,timeout=60);assert run.returncode==0,run.stderr
 manifest=json.loads((target/'manifest.json').read_text());span=1 if mode=='object' else 4
 assert manifest['widthMeters']==2*span and manifest['heightMeters']==span
 for slot,name in manifest['maps'].items():
  image=Image.open(target/name);source_size=Image.open(maps[slot]).size;assert image.size==tuple(n*span for n in source_size)
  assert hashlib.sha256((target/name).read_bytes()).hexdigest().upper()==manifest['sha256'][slot]
  if slot=='normal':
   n=np.array(image).astype(float)/255*2-1;assert np.max(np.abs(np.linalg.norm(n,axis=2)-1))<.015
   assert np.max(np.abs(n[:,:,1]))<.015,'Non-square material rotated by 90 degrees'
 output=Image.open(target/manifest['maps']['baseColor']);output.save(folder/(mode+'.png'))
 before=hashlib.sha256((target/'manifest.json').read_bytes()).hexdigest();again=subprocess.run([str(worker),str(path)],capture_output=True,text=True,timeout=10);assert again.returncode==0 and 'Cached' in again.stdout;assert before==hashlib.sha256((target/'manifest.json').read_bytes()).hexdigest()
 if mode=='stochastic':
  a=np.array(output).astype(float);correlation=float(np.corrcoef(a[:,:-128].ravel(),a[:,128:].ravel())[0,1]);assert correlation<.65,correlation
 reports.append(dict(mode=mode,span=span,sourceDensityPreserved=True,normalUnitAndRotation=True,cacheReused=True))
plain=Image.new('RGB',(512,512))
for y in range(4):
 for x in range(4):plain.paste(natural,(x*128,y*128))
plain.save(folder/'plain.png');contact=Image.new('RGB',(1024,512));contact.paste(plain,(0,0));contact.paste(Image.open(folder/'stochastic.png'),(512,0));contact.save(folder/'comparison.png')
(folder/'verified.json').write_text(json.dumps(reports,indent=2));print(json.dumps(reports))

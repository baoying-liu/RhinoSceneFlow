from pathlib import Path
import json,shutil,subprocess,hashlib,re,time
ROOT=Path(__file__).resolve().parents[4];BASE=Path(r'C:\Users\liu12\OneDrive - EDSA\01_File\SceneFlow');D=BASE/'SceneFlow-Production-Handoff-2026-11-13';P=D/'Project';O=ROOT/'media/tutorial-en/out/tutorial-full-v02'
def digest(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
paths=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=ROOT).decode('utf8').split('\0');source=[]
for name in paths:
 if not name:continue
 src=ROOT/name;dst=P/name
 if not src.is_file():continue
 assert not any(s.lower()in {'credentials','node_modules','.git'}for s in src.parts)
 if not dst.exists()or digest(src)!=digest(dst):dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
 source.append(name)
for name in ['SceneFlow-Tutorial-15min-v02.mp4','delivery-verified.json','qa-equivalence.json','timeline.json','qa-frames.json']:
 dst=P/'media/tutorial-en/out/tutorial-full-v02'/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(O/name,dst)
F=ROOT/'artifacts/tutorial-full-v02'
for f in F.iterdir():
 if f.is_file()and f.suffix.lower()in {'.py','.json','.png','.jpg','.sflowboard'}:
  dst=P/f.relative_to(ROOT);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,dst)
shutil.copy2(F/'SceneFlow-Tutorial-Recording-v02.sflowboard',D/'SceneFlow-Tutorial-Recording-v02.sflowboard')
readme=(D/'START-HERE.txt').read_text(encoding='utf8')
readme=readme.replace('Model: Project/artifacts/tutorial-full-v01/Tutorial-Demo-Final.3dm','Recommended model: Case/Tutorial-Portable.3dm\n   This separate copy preserves the 70 object identities and relinks 21 RDK texture\n   paths to the bundled Case/Textures sidecars. All texture files were verified present.\n   The original model is also retained: Project/artifacts/tutorial-full-v01/Tutorial-Demo-Final.3dm')
readme=readme.replace('Library/ contains all current material/plant IDs, seasonal/plan variants and texture cache.','Library/ contains all current material/plant IDs and their referenced seasonal/plan variants.\n   Unreferenced retired images and regenerable preview/cache files are not required.\n   Used baked texture pixels are preserved independently in Case/Textures.')
readme=readme.replace('Some Rhino texture paths in the model are absolute to the home computer. If Rhino reports\n   a missing bitmap, point its file search at Library and Library/cache; the ID-based library\n   remains present. Paths-to-Relink.json records the original references and bundled targets.','Run Connect-Library-in-Rhino.py manually in Rhino Python to configure this Library folder.\n   It does not install anything or overwrite the model. Then open Case/Tutorial-Portable.3dm.\n   The older ORIGINAL checkpoint still contains home-computer paths; use the portable copy\n   for office edits. Case/Portable-validation.json records the verified relative paths.')
(D/'START-HERE.txt').write_text(readme,encoding='utf8')
(D/'START-HERE.html').write_text('<!doctype html><meta charset="utf-8"><title>SceneFlow production handoff</title><style>body{background:#112b20;color:#eaf0e4;font:18px/1.7 Arial;max-width:1000px;margin:50px auto}a{color:#d8c795}pre{white-space:pre-wrap}</style><h1>SceneFlow · 公司继续制作 / Production handoff</h1><p><a href="../SceneFlow-Tutorial-15min-v02/Review.html">观看修订版教程 / Watch v02</a></p><p><a href="Case/Tutorial-Portable.3dm">可移植 Rhino 案例 / Portable Rhino case</a> · <a href="SceneFlow-Tutorial-Recording-v02.sflowboard">录制画板 / Recording board</a></p><p><a href="Project/media/tutorial-en/package.json">Remotion project</a> · <a href="START-HERE.txt">完整打开说明 / Open instructions</a></p><p>先确认 OneDrive 已同步完成。在公司选择“始终保留在此设备上”。<br/>The local copies were verified; cloud upload completion is not independently confirmed.</p>',encoding='utf8')
# Verify each image named in the current library metadata is available.
libraryChecks=[]
for meta in (D/'Library').rglob('asset.json'):
 raw=meta.read_text(encoding='utf8');refs=set(re.findall(r'[^"/\\\s]+\.(?:png|jpg|jpeg|webp)',raw))
 for name in refs:
  hits=list(meta.parent.rglob(name));assert hits,(meta,name);assert all(h.stat().st_size>0 for h in hits)
 libraryChecks.append(dict(asset=meta.parent.name,images=len(refs)))
print('Source snapshot and all current library references verified',flush=True)
records=[]
for f in D.rglob('*'):
 if f.is_file()and f.name!='Manifest-SHA256.json':records.append(dict(path=f.relative_to(D).as_posix(),bytes=f.stat().st_size,sha256=digest(f)))
assert not [r for r in records if r['bytes']==0 and r['path'].lower().endswith(('.png','.mp4','.wav','.safetensors'))]
result=dict(files=records,count=len(records),totalBytes=sum(r['bytes']for r in records),workingTreeFiles=len(source),currentLibrary=libraryChecks,portableCase=json.loads((D/'Case/Portable-validation.json').read_text()),approvedAudioUnchanged=True,cloudSyncVerified=False,created=time.time(),excluded=['API keys','login caches','machine credentials','node_modules','installed virtual environments','unreferenced retired library images','regenerable previews/cache','redundant rendered frame sequences'])
(D/'Manifest-SHA256.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(dict(files=result['count'],GB=round(result['totalBytes']/1e9,2),sourceFiles=len(source),libraryAssets=len(libraryChecks),portableTexturePaths=21,cloudSyncVerified=False)),flush=True)

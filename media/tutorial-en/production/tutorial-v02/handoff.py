"""Portable, explicit production handoff. Excludes accounts, keys and caches."""
from pathlib import Path
import os,json,shutil,subprocess,hashlib,time,sys
ROOT=Path(__file__).resolve().parents[4];BASE=Path(r'C:\Users\liu12\OneDrive - EDSA\01_File\SceneFlow');DEST=BASE/'SceneFlow-Production-Handoff-2026-11-13';PROJECT=DEST/'Project';DEST.mkdir(parents=True,exist_ok=True)
records=[]
def cp(src,dst):
 src=Path(src);dst=Path(dst)
 if 'Library' in dst.parts or 'Local-Voice-Model' in dst.parts:print('Copy '+str(src),flush=True)
 if not src.is_file():return
 if '_preview_rgb_' in src.name:return # derived cache; generated again from the bundled PNG
 assert not any(x.lower() in {'.git','node_modules','credentials','.cache','__pycache__'}for x in src.parts)
 assert src.suffix.lower()not in {'.key','.pfx','.p12','.pem','.dpapi'}
 if src.name.lower().startswith('.env') and src.name not in {'.env.example','.env.template'}:return
 dst.parent.mkdir(parents=True,exist_ok=True)
 try:
  if not dst.exists()or dst.stat().st_size!=src.stat().st_size:shutil.copy2('\\\\?\\'+str(src.resolve()),'\\\\?\\'+str(dst.resolve()))
 except OSError as e:
  print('Copy failed: '+str(src)+' -> '+str(dst),flush=True);raise
 records.append(dict(path=dst.relative_to(DEST).as_posix(),bytes=dst.stat().st_size,sha256=hashlib.sha256(dst.read_bytes()).hexdigest()))
files=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=ROOT).decode('utf8').split('\0') if '--finish-only'not in sys.argv else []
for name in files:
 if name:cp(ROOT/name,PROJECT/name)
print('Project source snapshot copied',flush=True)
# All public edit assets, including the accepted promotional film's sources.
for p in ((ROOT/'media/tutorial-en/public').rglob('*')if '--finish-only'not in sys.argv else []):
 if p.is_file():cp(p,PROJECT/p.relative_to(ROOT))
print('All Remotion public assets copied',flush=True)
F=ROOT/'artifacts/tutorial-full-v01'
for folder in (['captures','direct','orbit','compare-whole','compare-local','PSD','local-voice']if '--finish-only'not in sys.argv else []):
 for p in (F/folder).rglob('*'):
  if p.is_file():cp(p,PROJECT/p.relative_to(ROOT))
for p in (F.iterdir()if '--finish-only'not in sys.argv else []):
 if p.is_file()and (p.suffix.lower()in {'.png','.jpg','.mp4','.sflowboard','.py'}or p.name in ['Tutorial-Demo-Final.3dm','Tutorial-Working.3dm','Tutorial-Single-Material-and-Plants.3dm','material-job.json','plant-corrected-job.json','web-session.json','web-board-final.json','hd-review.json','audio-qa.json','prosody-check.json']):cp(p,PROJECT/p.relative_to(ROOT))
F2=ROOT/'artifacts/tutorial-full-v02'
for p in F2.iterdir():
 if p.is_file()and p.suffix.lower()in {'.png','.jpg','.json','.py'}:cp(p,PROJECT/p.relative_to(ROOT))
# Keep finished and review exports, never the redundant 27k-frame encodes.
for p in ((ROOT/'media/tutorial-en/out').rglob('*')if '--finish-only'not in sys.argv else []):
 if p.is_file()and not any(x in {'held-frames','all-frames'}for x in p.parts)and p.suffix.lower()in {'.mp4','.srt','.csv','.txt','.html','.json','.png','.jpg','.wav'}:
  if p.name.endswith('.tmp')or p.name=='SceneFlow-Tutorial-15min-v02.mp4':continue
  cp(p,PROJECT/p.relative_to(ROOT))
print('Case, captures, narration and review exports copied',flush=True)
library=Path(r'C:\Users\liu12\OneDrive - EDSA\01_File\SceneFlow立面\Hillside-Promo-2026-11-12\Library')
for folder in ['assets','Plants/assets']:
 for asset in (library/folder).iterdir():
  if not asset.is_dir()or not(asset/'asset.json').exists():continue
  text=(asset/'asset.json').read_text(encoding='utf8')
  for p in asset.rglob('*'):
   if p.is_file()and(p.name=='asset.json'or(p.suffix.lower()in {'.png','.jpg','.jpeg','.webp'}and p.name in text)):cp(p,DEST/'Library'/p.relative_to(library))
print('All active library references copied; unused retired images and derived caches excluded',flush=True)
# Explicit voice allowlist. No cloud response, credential or authorisation file.
private=Path(os.environ['LOCALAPPDATA'])/'RhinoSceneFlow/production/voice-private'
for name in ['baoying-reference-24k-mono.wav','reference-transcript-small.json']:cp(private/name,DEST/'Private-Voice-Reference'/name)
cp(BASE/'Pine Tree Ln.m4a',DEST/'Private-Voice-Reference/Pine Tree Ln.m4a')
models=Path(os.environ['LOCALAPPDATA'])/'RhinoSceneFlow/qwen-models/Qwen3-TTS-12Hz-1.7B-Base'
for p in models.rglob('*'):
 if p.is_file()and '.cache'not in p.parts:cp(p,DEST/'Local-Voice-Model/Qwen3-TTS-12Hz-1.7B-Base'/p.relative_to(models))
(DEST/'Local-Voice-Model/requirements-reference.txt').write_text('qwen-tts==0.1.1\ntransformers==4.57.3\nsoundfile==0.14.0\nnumpy==2.5.4\naccelerate==1.12.0\n# Tested Torch: 2.11.0+cu128 and torchaudio 2.11.0+cu128.\n# Install the Torch build appropriate to the office GPU/driver.\n',encoding='utf8')
readme='''SCENEFLOW — PORTABLE PRODUCTION HANDOFF / 公司继续制作说明

1. VIEW / 看修订版
   Open ../SceneFlow-Tutorial-15min-v02/Review.html or the MP4 beside it.
   The accepted promotional film remains ../SceneFlow-Introduction-v07.mp4.

2. EDIT VIDEO / 修改视频
   Open Project/media/tutorial-en in VS Code.
   With Node.js installed: npm ci, then npm run dev.
   Choose SceneFlow-Tutorial-Full-v02. The older v01 and promotional compositions remain.
   The complete public assets, source captures, 42 accepted voice WAVs and subtitles are included.
   Edit src/TutorialFullSceneV02.tsx for framing; production/tutorial-v02/revise.py contains
   cue-aligned shots, scroll offsets and cursor targets. Running revise.py regenerates
   src/TutorialFullV02.tsx, so preserve manual timeline edits before doing that.
   production/tutorial-v02/render.cjs + encode.py reproduce the optimised 30-fps export.
   Standard alternative: npx remotion render SceneFlow-Tutorial-Full-v02 out/Tutorial.mp4
   Never copy node_modules or a virtual environment from another computer; reinstall dependencies.

3. RHINO / 案例与素材
   Model: Project/artifacts/tutorial-full-v01/Tutorial-Demo-Final.3dm
   Earlier white/single-material checkpoints are beside it. PSD is in PSD/.
   Library/ contains all current material/plant IDs, seasonal/plan variants and texture cache.
   Install SceneFlow on the office computer normally; use its original Rhino MCP Platform.
   Configure material_configure with directory=<absolute path to this Library folder>.
   MaterialDirectory is a machine preference, NOT the same path on every computer.
   Some Rhino texture paths in the model are absolute to the home computer. If Rhino reports
   a missing bitmap, point its file search at Library and Library/cache; the ID-based library
   remains present. Paths-to-Relink.json records the original references and bundled targets.
   Do not overwrite the office library or the original model. Save a new case after relinking.
   The archive contains the plugin source and build scripts; it does not auto-install into Rhino.

4. WEB / 画板
   Import Project/artifacts/tutorial-full-v01/SceneFlow-Tutorial.sflowboard in Web Studio.
   This is the completed original-to-4K case. The separately included v02 recording board
   also contains the extra blank drafts used to demonstrate real annotation operations.
   Use the board package, not an old browser URL/token; each machine starts its own service.

5. VOICE / 配音
   Existing WAVs are ready for editing. v02 copies the accepted v01 AAC track unchanged.
   Private-Voice-Reference contains your recording + clean reference and transcript.
   Local-Voice-Model includes the downloaded Base model and speech tokenizer, avoiding another
   model download. They retain their upstream licence (see the bundled model README).
   To regenerate with production/tutorial-v01/local_voice.py, install the Qwen dependencies;
   copy the model to %LOCALAPPDATA%/RhinoSceneFlow/qwen-models/ and the clean reference files
   to %LOCALAPPDATA%/RhinoSceneFlow/production/voice-private/. No cloud API key is needed.
   Keep these private voice files out of public GitHub repositories.

6. SYNC / 同步
   This verifies the local OneDrive copy only. Check OneDrive has completed uploading before
   turning off this computer. On the office computer choose “Always keep on this device”.
   Windows/Rhino/Node/CUDA runtimes, installed accounts, API keys and login caches are intentionally
   not copied. Machine-specific library paths and dependencies may need reconfiguration.
'''
(DEST/'START-HERE.txt').write_text(readme,encoding='utf8')
oldpaths=json.loads((F2/'model-textures.json').read_text(encoding='utf8'))
(DEST/'Paths-to-Relink.json').write_text(json.dumps([dict(original=p,bundled='Library/'+p.replace('\\','/').split('/Library/',1)[1])for p in oldpaths],ensure_ascii=False,indent=2),encoding='utf8')
(DEST/'Manifest-SHA256.json').write_text(json.dumps(dict(files=records,count=len(records),totalBytes=sum(x['bytes']for x in records),created=time.time(),cloudSyncVerified=False,excluded=['credentials','API keys','login caches','virtual environments','node_modules','.git','redundant render frames']),ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(dict(destination=str(DEST),files=len(records),GB=round(sum(x['bytes']for x in records)/1e9,2))),flush=True)

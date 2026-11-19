from pathlib import Path
import json,shutil,hashlib,csv
ROOT=Path(__file__).resolve().parents[4];M=ROOT/'media/tutorial-en';O=M/'out/tutorial-full-v02';BASE=Path(r'C:\Users\liu12\OneDrive - EDSA\01_File\SceneFlow');D=BASE/'SceneFlow-Tutorial-15min-v02';D.mkdir(exist_ok=True)
assert(O/'delivery-verified.json').exists()
files=[(O/'SceneFlow-Tutorial-15min-v02.mp4','SceneFlow-Tutorial-15min-v02.mp4'),(O/'delivery-verified.json','Video-validation.json'),(O/'timeline.json','timeline.json'),(O/'qa-equivalence.json','QA-equivalence.json')]
for name in ['SceneFlow-Tutorial-English.srt','Script-EN-ZH.csv','Chapters.txt']:files.append((M/'out/tutorial-full-v01'/name,name))
for name in ['SceneFlow-Tutorial-Result-4K.png','SceneFlow-Tutorial.sflowboard']:files.append((ROOT/'artifacts/tutorial-full-v01'/name,name))
verified=[]
for src,name in files:
 shutil.copy2(src,D/name);a=hashlib.sha256(src.read_bytes()).hexdigest();b=hashlib.sha256((D/name).read_bytes()).hexdigest();assert a==b;verified.append(dict(file=name,bytes=src.stat().st_size,sha256=b))
review=(BASE/'SceneFlow-Tutorial-15min-v01/Review.html').read_text(encoding='utf8').replace('SceneFlow-Tutorial-15min-v01.mp4','SceneFlow-Tutorial-15min-v02.mp4').replace('first cut','visual revision 02').replace('此版使用真实界面剪辑；安装窗口为示意。配音内容已做 ASR 核对，语气、相似度和吞音仍需人工试听确认。','修订 02：持续显示鼠标、补齐下拉菜单切换、描述区滚动、Web 来源关系与工具指引。保留已认可的上一版配音，音轨字节核对一致。安装窗口仍为示意，主体使用真实界面剪辑。')
review=review.replace('</main>','<p><a href="../SceneFlow-Production-Handoff-2026-11-13/START-HERE.txt">公司电脑工程打开说明 / Production handoff</a></p></main>')
(D/'Review.html').write_text(review,encoding='utf8')
(D/'README.txt').write_text('SceneFlow — visual revision 02\n15:01.4 · 1920 × 1080 · 30 fps · English narration/subtitles.\n\nChanges: persistent guided cursor; real dropdown entry at native tool changes; description and parameter framing with visible content pans; Web lineage overview before focused work; Arrow/Text/reference actions; actual divider tracking; editable 4K controls and real completed tile review.\nAudio is copied unchanged from the v01 approved by the user.\nOriginal v01 is retained beside this folder.\n\nThe capture is an edited demonstration using genuine UI states plus an editorial cursor. Installer visuals are labelled illustrations.\nComplete editable source, all public assets, original captures, case checkpoints, material/plant library, board, voice reference and local model: ../SceneFlow-Production-Handoff-2026-11-13/\nRead START-HERE.txt there for office setup, library paths and dependencies.\nLocal file verification does not confirm OneDrive cloud upload has finished.\n',encoding='utf8')
(D/'Delivery-verification.json').write_text(json.dumps(verified,indent=2),encoding='utf8')
rows=json.loads((O/'timeline.json').read_text(encoding='utf8'))
with(D/'Visual-cue-review.csv').open('w',encoding='utf-8-sig',newline='')as f:
 w=csv.writer(f);w.writerow(['Cue','Start seconds','Narration','Screens / offsets','Cursor actions / cue-relative seconds'])
 for c in rows:w.writerow([c['id'],c['start']/30,c['en'],json.dumps(c['shots'],ensure_ascii=False),json.dumps(c['cursor'],ensure_ascii=False)])
(BASE/'SceneFlow-Tutorial-Latest.html').write_text('<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=SceneFlow-Tutorial-15min-v02/Review.html"><a href="SceneFlow-Tutorial-15min-v02/Review.html">Open revised SceneFlow tutorial</a>',encoding='utf8')
print(json.dumps(dict(destination=str(D),sha256=verified[0]['sha256'],bytes=verified[0]['bytes'])))

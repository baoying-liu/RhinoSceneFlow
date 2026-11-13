"""Build an editable, cue-aligned tutorial from actual captured software states."""
from pathlib import Path
import json,re,shutil,csv,math,difflib
import wave
ROOT=Path(__file__).resolve().parents[4]
F=ROOT/'artifacts/tutorial-full-v01';P=ROOT/'media/tutorial-en/public/case/tutorial-full-v01'
S=Path(__file__).parent;data=json.loads((S/'script.json').read_text(encoding='utf8'))
DEL=ROOT/'media/tutorial-en/out/tutorial-full-v01';DEL.mkdir(parents=True,exist_ok=True)
def native(name,focus='top',right=None,menu=False,note=''):
 return dict(kind='native',left=name+'-'+focus+'.jpg',right=(right or name)+'-view.jpg',menu=menu,note=note)
def photo(name):return dict(kind='photo',left='export-final-controls-middle.jpg',right=name+'.png')
def web(name,focus=120,video=None,note=''):
 return dict(kind='web',image=name+'.png',focus=focus,video=video,note=note)
shots={
'T01-01':[(0,dict(kind='intro',image='complete-case-view.jpg'))],
'T02-01':[(0,dict(kind='github',image='github-release.png'))],
'T02-02':[(0,dict(kind='setup',step=0)),(6,dict(kind='setup',step=1)),(12,dict(kind='setup',step=2))],
'T02-03':[(0,dict(kind='establish',image='white-model-full.jpg')),(8,native('white-model',note='Preview release · v0.23.3'))],
'T03-01':[(0,native('settings',right='complete-case',menu=True))],
'T03-02':[(0,native('settings','middle',right='complete-case',note='AI sign-in ≠ Rhino MCP connection'))],
'T03-03':[(0,native('settings',right='complete-case',note='Resolve the check before generating'))],
'T04-01':[(0,native('white-model',menu=True,note='Tools on the left · model view on the right'))],
'T05-01':[(0,native('white-model',menu=True)),(5,native('white-selected',right='white-selected',note='One selected wall · object scope'))],
'T05-02':[(0,native('material-draft','middle',right='white-selected'))],
'T05-03':[(0,native('material-draft',right='white-selected',note='Find existing assets first · optional reference image'))],
'T05-04':[(0,native('material-generating','middle',right='white-selected',note='Generation wait shortened')),(9,native('material-result','middle',right='white-selected'))],
'T05-05':[(0,native('material-result','bottom',right='white-selected')),(9,native('material-applied','bottom',right='material-applied',note='Material applied · physical-scale UVs ready'))],
'T06-01':[(0,native('material-dimensions-final','bottom',right='material-applied',menu=True,note='Check and set texture area · 1.2 × 2.4 m'))],
'T06-02':[(0,native('material-dimensions-final','bottom',right='material-applied',note='Check dimensions before changing geometry'))],
'T07-01':[(0,native('plant-draft','middle',right='material-applied',menu=True)),(10,native('plant-generating','middle',right='material-applied',note='One elevation image · a separate plan variant · wait shortened'))],
'T07-02':[(0,native('plant-library-final',right='material-applied',menu=True)),(6,dict(kind='plants',left='plant-library-final-top.jpg'))],
'T07-03':[(0,native('plant-library-final','middle',right='material-applied')),(7,native('plant-properties-final','middle',right='plant-scatter',note='Carrier surface / mesh · world Z stays upright')),(17,native('plant-properties-final','bottom',right='plant-manual'))],
'T07-04':[(0,native('plant-properties-final','middle',right='plant-scatter',menu=True,note='Select group → Properties → density / scale / seed')),(10,native('plant-properties-final','lower',right='plant-scatter-variation',note='Avoidance checks the planting base and clearance'))],
'T07-05':[(0,native('plant-properties-final',right='plant-manual',note='Group parameters and individual editing are separate'))],
'T08-01':[(0,native('complete-case',right='complete-case',note='Prepared checkpoint · same model, remaining work completed'))],
'T08-02':[(0,dict(**native('plant-controls-final',right='complete-case',note='Actual Rhino camera movement'),video='orbit.mp4',videoAt=2,videoEnd=8)),(8,native('plant-controls-final',right='orbit-end'))],
'T08-03':[(0,native('plant-display-final','middle',right='complete-plan',menu=True,note='Plan starts at 75° · lift ratio 0.20'))],
'T08-04':[(0,native('plant-display-final','middle',right='complete-rendered',note='Rendered · surface appearance')),(8,native('plant-display-final','middle',right='complete-arctic',note='Arctic · form and massing'))],
'T09-01':[(0,native('export-overview',right='complete-case',menu=True))],
'T09-02':[(0,native('export-final-controls',right='complete-case')),(8,native('export-final-controls','middle',right='complete-case',note='Output dimensions and PSD channels are separate'))],
'T09-03':[(0,native('export-final-controls','middle',right='complete-case',note='✓ Include in export    Eye = initial PSD visibility')),(10,native('export-final-controls','bottom',right='complete-case',note='Export completed · actual layered PSD'))],
'T10-01':[(0,photo('photo-raw')),(9,photo('photo-no-plants')),(13,photo('photo-raw'))],
'T10-02':[(0,photo('photo-no-plant-shadow')),(5,photo('photo-no-shadow')),(10,photo('photo-materials-expanded'))],
'T10-03':[(0,photo('photo-arctic-clean')),(6,photo('photo-depth')),(13,photo('photo-material-colors'))],
'T11-01':[(0,web('web-whole-list',100,note='Same PSD → traceable Web board'))],
'T11-02':[(0,web('web-whole-list')),(10,web('web-canvas-fit',120,note='List and canvas · one project'))],
'T11-03':[(0,web('web-draft')),(7,web('web-whole-list',300))],
'T11-04':[(0,web('web-participation-detail',100,note='PSD visibility and AI participation are independent'))],
'T11-05':[(0,web('web-whole-list',100,video='compare-whole.mp4',note='Actual divider drag · result left, parent right'))],
'T12-01':[(0,web('web-draft')),(6,web('web-canvas-fit'))],
'T12-02':[(0,web('web-arrow',300)),(6,web('web-annotated-reference',300,note='Arrow + text + material reference · inside context frame'))],
'T12-03':[(0,web('web-annotated-reference',300)),(10,web('web-preflight-reference',300,note='Actual request: 2 annotations + 1 reference'))],
'T12-04':[(0,web('web-local-result',200,video='compare-local.mp4',note='Compare the revision with its parent'))],
'T13-01':[(0,web('web-hd-settings',300,note='4096 px long edge · overlapping tiles'))],
'T13-02':[(0,web('web-hd-task',300,note='Inspect task status and tile review')),(10,web('web-hd-complete',150,note='Completed result · 4096 × 2304 pixels'))],
'T13-03':[(0,web('web-final-export',100,note='Export the image · save the board')),(12,dict(kind='outro',image='final-4k.jpg'))],
}
def display(text):
 for a,b in [('Scene Flow','SceneFlow'),('P S D','PSD'),('M C P','MCP'),('A I','AI'),('U V','UV'),('E X E','EXE')]:text=text.replace(a,b)
 return text
def captions(cue,dur):
 path=F/'local-voice'/(cue['id']+'.asr.json')
 segments=json.loads(path.read_text()) if path.exists() else []
 spoken=[w for s in segments for w in s['words']]
 words=display(cue['en']).split()
 norm=lambda x:re.sub('[^a-z0-9]','',x.lower())
 a=[norm(w) for w in words];b=[norm(w['word']) for w in spoken];mapping={}
 for match in difflib.SequenceMatcher(None,a,b,autojunk=False).get_matching_blocks():
  for i in range(match.size):mapping[match.a+i]=spoken[match.b+i]['start']
 mapping[-1]=0;mapping[len(words)]=max(.1,dur-.2)
 times=[]
 for i in range(len(words)):
  if i in mapping:t=mapping[i]
  else:
   lo=max(k for k in mapping if k<i);hi=min(k for k in mapping if k>i);t=mapping[lo]+(mapping[hi]-mapping[lo])*(i-lo)/(hi-lo)
  times.append(max(times[-1] if times else 0,t))
 # Phrase pages use genuine ASR timing anchors and the approved written spelling.
 result=[];i=0
 while i<len(words):
  j=min(i+8,len(words))
  for k in range(i+3,j):
   if words[k-1].endswith(('.', '?', '!', ';')):j=k;break
  st=times[i]+.7;en=(times[j] if j<len(words) else dur)+.7
  result.append(dict(text=' '.join(words[i:j]),startMs=round(st*1000),endMs=round(max(st+.25,en)*1000),timestampMs=None,confidence=None,pageBreakAfter=True));i=j
 return result
timeline=[];start=0
for cue in data['cues']:
 f=F/'local-voice'/(cue['id']+'.wav');assert f.exists(),f'Missing audio {f}'
 with wave.open(str(f)) as wav:dur=wav.getnframes()/wav.getframerate()
 length=max(cue['budget'],dur+1.4);frames=math.ceil(length*30)
 shutil.copy2(f,P/f.name)
 cs=captions(cue,dur);entry=dict(**cue,start=start,frames=frames,voice=dur,captions=cs,shots=[dict(at=at,**v) for at,v in shots[cue['id']]])
 timeline.append(entry);start+=frames
(P/'timeline.json').write_text(json.dumps(timeline,ensure_ascii=False,indent=2),encoding='utf8')
(DEL/'timeline.json').write_text(json.dumps(timeline,ensure_ascii=False,indent=2),encoding='utf8')
def stamp(sec,comma=False):
 ms=round(sec*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000);return f'{h:02}:{m:02}:{s:02}{"," if comma else "."}{ms:03}'
lines=[];idx=1
for c in timeline:
 for cap in c['captions']:
  lines.extend([str(idx),stamp(c['start']/30+cap['startMs']/1000,True)+' --> '+stamp(c['start']/30+cap['endMs']/1000,True),cap['text'],'']);idx+=1
(DEL/'SceneFlow-Tutorial-English.srt').write_text('\n'.join(lines),encoding='utf8')
with (DEL/'Script-EN-ZH.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f);w.writerow(['Cue','Start','End','English','中文对照'])
 for c in timeline:w.writerow([c['id'],stamp(c['start']/30),stamp((c['start']+c['frames'])/30),display(c['en']),c['zh']])
chapters=[]
for ch in data['chapters']:
 c=next(c for c in timeline if c['chapter']==ch['id']);chapters.append(stamp(c['start']/30).split('.')[0]+' '+ch['title'])
(DEL/'Chapters.txt').write_text('\n'.join(chapters),encoding='utf8')
# Literal cue instances retain independent timing in Remotion Studio.
jsx=["import React from 'react';","import {AbsoluteFill,Sequence,Audio,staticFile} from 'remotion';","import {TutorialScene} from './TutorialFullScene';","import {BasicCaptions} from './basic-captions.element';",f'export const tutorialFullFrames={start};',"export const TutorialFullV01:React.FC=()=> <AbsoluteFill style={{background:'#10251d'}}>" ]
for c in timeline:
 props=json.dumps({k:c[k] for k in ['id','chapter','shots']},ensure_ascii=False)
 title=next(ch['title'] for ch in data['chapters'] if ch['id']==c['chapter'])
 jsx.append(f'<Sequence name={json.dumps(c["id"]+" · "+title)} from={{{c["start"]}}} durationInFrames={{{c["frames"]}}}>')
 jsx.append('<TutorialScene {...'+props+'} title='+json.dumps(title)+'/>')
 jsx.append(f'<Sequence from={{21}} layout="none"><Audio src={{staticFile("case/tutorial-full-v01/{c["id"]}.wav")}} /></Sequence>')
 jsx.append('<div style={{position:"absolute",left:310,bottom:22,transform:"scale(.53)",transformOrigin:"bottom left"}}><BasicCaptions name="English subtitles" width={2450} combineTokensWithinMilliseconds={0} captions={'+json.dumps(c['captions'],ensure_ascii=False)+'}/></div>')
 jsx.append('</Sequence>')
jsx.append('</AbsoluteFill>;')
(ROOT/'media/tutorial-en/src/TutorialFullV01.tsx').write_text('\n'.join(jsx),encoding='utf8')
print(json.dumps(dict(cues=len(timeline),seconds=start/30,frames=start)))

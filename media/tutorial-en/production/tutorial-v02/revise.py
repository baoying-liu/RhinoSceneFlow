"""Visual revision only. Preserve the approved v01 narration and caption timing."""
from pathlib import Path
import json,shutil,re
ROOT=Path(__file__).resolve().parents[4];M=ROOT/'media/tutorial-en';O=M/'out/tutorial-full-v02';P=M/'public/case/tutorial-full-v02';F=ROOT/'artifacts/tutorial-full-v02'
rows=json.loads((M/'out/tutorial-full-v01/timeline.json').read_text(encoding='utf8'))
def N(name,scroll=0,right='complete-case',pan=None,nav=None,note=''):
 return dict(kind='native',left=name,scroll=scroll,pan=pan or [],right=right+'-view.jpg',nav=nav,note=note)
def W(name,focus=120,full=False,pan=None,note='',video=None):
 return dict(kind='web',image=name+'.png',focus=focus,full=full,pan=pan or [],note=note,video=video)
def E(t,x,y,label='',space='screen',click=False):return dict(at=t,x=x,y=y,label=label,space=space,click=click)
def B(t,x,y,label='',click=False):return E(t,x,y,label,'body',click)
def R(t,x,y,label='',click=False):return E(t,x,y,label,'webMain',click)
def L(t,x,y,label='',click=False):return E(t,x,y,label,'webLeft',click)
def H(previous,row):return dict(previous=previous,row=row)
shots={
'T02-03':[(0,dict(kind='establish',image='white-model-full.jpg')),(8,N('white-model',0,'white-model'))],
'T03-01':[(0,N('settings',0,'white-model',nav=H('white-model',8)))],
'T03-02':[(0,N('settings',570,'white-model'))],
'T03-03':[(0,N('settings',0,'white-model'))],
'T04-01':[(0,N('white-model',0,'white-model',nav=H('settings',0)))],
'T05-01':[(0,N('white-model',0,'white-model')),(5,N('white-selected',0,'white-selected'))],
'T05-02':[(0,N('material-draft',850,'white-selected',pan=[[0,850],[2,1000]]))],
'T05-03':[(0,N('material-draft',1000,'white-selected',pan=[[0,1000],[6,0]],note='Reference images are optional · Reuse checks the local library'))],
'T05-04':[(0,N('material-draft',1000,'white-selected')),(3,N('material-generating',400,'white-selected',note='Generation wait shortened')),(10,N('material-result',650,'white-selected'))],
'T05-05':[(0,N('material-result',1050,'white-selected')),(12,N('material-applied',1050,'material-applied',note='Applied to the selected wall · UV preparation completed'))],
'T06-01':[(0,N('material-dimensions-final',1000,'material-applied',nav=H('material-applied',1),note='Physical texture area: 1.2 × 2.4 m'))],
'T06-02':[(0,N('material-dimensions-final',1000,'material-applied'))],
'T07-01':[(0,N('plant-draft',1000,'material-applied',nav=H('material-dimensions-final',0))),(12,N('plant-generating',1050,'material-applied',note='Botanical check + generation · wait shortened'))],
'T07-02':[(0,N('plant-library-final',0,'material-applied',nav=H('plant-draft',3))),(7,dict(kind='plants',left='plant-library-final',scroll=0))],
'T07-03':[(0,N('plant-library-final',1070,'material-applied')),(7,N('plant-library-final',580,'material-applied',note='Add the selected asset to the planting palette')),(10,N('plant-library-final',1070,'material-applied')),(12,N('plant-library-final',1070,'plant-scatter',note='Actual scattered planting on the carrier surface')),(15,N('plant-properties-final',1000,'plant-manual',nav=H('plant-library-final',5)))],
'T07-04':[(0,N('plant-properties-final',740,'plant-scatter')),(10,N('plant-properties-final',1000,'plant-scatter-variation',note='Density, independent seeds and size limits'))],
'T07-05':[(0,N('plant-properties-final',0,'plant-manual'))],
'T08-01':[(0,N('complete-case',0,'complete-case',note='Prepared checkpoint · same model; remaining work already completed'))],
'T08-02':[(0,dict(**N('plant-controls-final',0,'complete-case',nav=H('plant-properties-final',3),note='Actual Rhino camera movement'),video='orbit.mp4',videoAt=3.5,videoEnd=9.5)),(9.5,N('plant-controls-final',0,'orbit-end'))],
'T08-03':[(0,N('plant-display-final',500,'complete-plan',nav=H('plant-controls-final',8),note='Plan starts at 75° · lift = actual plant height × 0.20'))],
'T08-04':[(0,N('plant-display-final',500,'complete-rendered',note='Viewport mode: Rendered')),(8,N('plant-display-final',500,'complete-arctic',note='Viewport mode: Arctic · export channels stay separate'))],
'T09-01':[(0,N('export-layers-expanded',0,'complete-case',nav=H('plant-display-final',6)))],
'T09-02':[(0,N('export-layers-expanded',430,'complete-case')),(10,N('export-layers-expanded',830,'complete-case'))],
'T09-03':[(0,N('export-layers-expanded',830,'complete-case',note='Checkbox: export inclusion · Eye: initial PSD visibility')),(11,N('export-layers-expanded',1070,'complete-case',note='Actual export was completed before opening the PSD'))],
'T11-01':[(0,N('post-v02',0,'complete-case',nav=H('export-layers-expanded',7))),(5,W('web-overview',0,True,note='Actual source → whole image → local revision → 4K lineage'))],
'T11-02':[(0,W('web-whole-params',120,True)),(8,W('web-overview',120,True)),(14,W('web-whole-canvas',120))],
'T11-03':[(0,W('web-source',500)),(3,W('web-child-blank',120)),(7,W('web-child-description',300,note='A new draft has blank instructions; the approved parent stays unchanged'))],
'T11-04':[(0,W('web-participation-detail',100))],
'T11-05':[(0,dict(**W('web-whole-end',100,video='compare-whole.mp4',note='Actual comparison drag · result left / parent right'),videoAt=4))],
'T12-01':[(0,W('web-overview',0,True)),(3,W('web-local-blank',120)),(6,W('web-local-applied',120))],
'T12-02':[(0,W('web-arrow-tool',300)),(3,W('web-arrow-drawn',300)),(5,W('web-text-drawn',300)),(9,W('web-reference-added',300,note='Arrow + text + reference · captured in the image context frame'))],
'T12-03':[(0,W('web-reference-added',300)),(10,W('web-preflight-reference',300,note='Recorded generated revision inputs: 2 annotations + 1 reference'))],
'T12-04':[(0,dict(**W('web-local-end',200,video='compare-local.mp4',note='Actual revision compared with its parent'),videoAt=3.5))],
'T13-01':[(0,W('web-hd-settings',300,note='4K output · overlapping detail tiles'))],
'T13-02':[(0,W('web-tiles-review',0,True,note='Actual completed tile review · inspect before accepting')),(10,W('web-hd-complete',150,note='Completed: 4096 × 2304 · all eight tiles passed'))],
'T13-03':[(0,W('web-final-export',100,True)),(3,W('web-hd-complete',100,True)),(12,dict(kind='outro',image='final-4k.jpg'))]
}
# Coordinates are in the captured body or original browser pixels, never guessed
# after independently cropping the pointer. Runtime applies the same transform.
events={
'T01-01':[E(0,1440,650),E(4,1150,580,'One model → complete workflow')],
'T02-01':[E(0,520,260),E(3,1370,500,'Release assets'),E(6,1280,565,'Windows EXE',click=True)],
'T02-02':[E(0,310,300,'Save and close Rhino'),E(6,720,380,'Component checks'),E(12,730,450,'Reopen Rhino')],
'T02-03':[E(0,190,290),E(6,620,160,'SceneFlow tool dropdown'),E(9,300,150)],
'T03-01':[B(4,330,352,'Check environment and sign-in',True),B(9,250,490,'AI account access'),B(14,270,630,'Read the actual check result')],
'T03-02':[B(0,275,920,'Rhino MCP connection'),B(7,280,1018,'Original MCP configuration guide',True)],
'T03-03':[B(0,320,350,'Resolve the failed check first'),B(7,290,490,'AI account settings')],
'T04-01':[E(4,260,152,'Tool dropdown'),E(8,1140,520,'Model viewport'),E(12,260,152,'Use this dropdown to change tools')],
'T05-01':[E(0,1130,490),E(4.5,1295,565,'Select the wall',click=True),E(9,1315,610,'One selected target')],
'T05-02':[B(0,280,1250,'Material description'),B(5,190,1290,'Surface + grain + physical size'),B(11,320,1325,'Weathered vertical cedar')],
'T05-03':[B(0,34,1375,'Attach a reference',True),B(7,14,72,'Reuse existing assets first'),B(12,240,155,'Local material library')],
'T05-04':[B(0,565,1375,'Submit description',True),B(4,270,660,'Actual task feedback'),B(11,300,1010,'Inspect the generated texture')],
'T05-05':[B(0,290,1550,'Application scope',True),B(5,250,1550,'Object / layer'),B(10,300,1608,'Apply selected material',True),E(13,1330,620,'Inspect the selected wall')],
'T06-01':[B(4,250,1502,'Physical width'),B(8,250,1551,'Physical height'),E(12,1300,580,'Compare against familiar dimensions')],
'T06-02':[B(0,250,1502,'Texture width / height'),E(5,1320,610,'Physical-scale UV mapping'),B(11,250,1551,'Correct dimensions; keep model geometry')],
'T07-01':[B(4,280,1220,'Scientific name + plant description'),B(8,555,1375,'Generate the plant',True),B(14,270,1550,'Identity / reuse / generation feedback')],
'T07-02':[B(4,130,500,'Betula nigra · scientific name'),E(8,1110,470,'Elevation image'),E(13,1550,490,'Separate plan image')],
'T07-03':[B(0,280,1730,'Place continuously · Esc to finish',True),E(4,1270,680,'Choose a carrier position',click=True),B(8,265,765,'Add to planting palette',True),B(11,280,1675,'Scatter on surface',True),E(12.5,1275,620,'Surface / mesh carrier'),B(19,280,1675,'Scatter on surface')],
'T07-04':[B(0,265,870,'Density'),B(4,260,1050,'Minimum scale'),B(7,270,1200,'Maximum scale'),B(11,255,950,'Layout seed'),B(15,170,1430,'Avoidance zones')],
'T07-05':[B(0,300,85,'Enter individual plant editing'),E(5,1260,620,'Select the group for shared settings'),B(10,300,85,'Individual editing is separate',True)],
'T08-01':[E(0,1230,560,'Prepared checkpoint'),E(10,1240,680,'Same building and site')],
'T08-02':[E(4,1370,500,'Orbit the Rhino camera'),E(10,1390,600,'Plant positions remain fixed')],
'T08-03':[B(4,265,544,'Camera-facing mode'),B(7,290,843,'Plan-image angle threshold'),B(12,270,931,'Plan lift ratio: 0.20')],
'T08-04':[E(0,1160,450,'Rendered preview'),E(8,1160,450,'Arctic preview'),B(13,275,544,'Preview ≠ export channels')],
'T09-01':[B(4,220,218,'Named View'),B(8,530,15,'Create view'),B(12,220,218,'Name the view clearly')],
'T09-02':[B(0,170,633,'Width'),B(3,330,633,'Height'),B(6,265,730,'Rendered preview'),B(11,190,1050,'PSD channels · top to bottom')],
'T09-03':[B(0,164,1045,'Checkbox: include'),B(4,125,1045,'Eye: initially visible'),B(12,250,1575,'Output folder'),B(16,260,1732,'Export selected views as PSD',True)],
'T10-01':[E(0,1160,170,'Actual exported PSD'),E(8,1560,606,'Plants group visibility',click=True),E(13,1560,606,'Restore plants visibility',click=True)],
'T10-02':[E(0,1560,702,'Separated plant shadow'),E(5,1560,734,'Other shadows'),E(10,1582,670,'Material children',click=True),E(14,1640,800,'Independent material layers')],
'T10-03':[E(0,1560,702,'Arctic'),E(6,1560,734,'Depth'),E(13,1560,766,'Material colors')],
'T11-01':[B(4,320,105,'Open Web Studio',True),E(6,380,450,'Source PSD'),E(10,770,450,'Whole image'),E(14,1380,450,'High resolution · linked ancestry')],
'T11-02':[E(0,900,35,'List view'),E(5,1750,470,'Parameters'),E(8,975,35,'Canvas view',click=True),E(11,1090,450,'Revision relationships'),R(15,1320,100,'Fit selected',True)],
'T11-03':[L(0,1750,1048,'Create proposal',True),L(4,1770,315,'Input from the original'),L(8,1740,475,'Write the visual brief'),L(13,1740,530,'Review instructions before generation')],
'T11-04':[L(0,1740,280,'PSD · AI participation'),L(4,1640,460,'Participation checkbox'),L(9,1760,590,'Channel usage / guidance')],
'T11-05':[R(0,920,620,'Compare with parent'),R(7,1180,620,'Inspect roof and openings'),R(11,1080,790,'Paths, plants and surfaces')],
'T12-01':[E(0,765,447,'Use the completed parent'),L(3.5,1750,315,'New child · parent input'),L(5,1730,392,'Use input as annotation background',True),R(8,1320,100,'Fit selected',True),R(12,900,650,'Working image · original stays traceable')],
'T12-02':[R(0,392,100,'Arrow tool',True),R(1.8,1180,470,'Draw toward the target'),R(3,935,675,'Arrow points to the façade'),R(4.3,425,100,'Text tool',True),R(6,1110,430,'Short local instruction'),L(9,1760,700,'Add reference image'),R(12,620,490,'Reference + instruction inside the boundary')],
'T12-03':[R(0,1395,307,'Context boundary'),R(5,1480,930,'Resources may remain outside'),L(10.5,1740,390,'Review actual inputs',True)],
'T12-04':[R(0,920,615,'Result versus parent'),R(6,1020,660,'Marked façade'),L(11,1730,490,'Revise the instructions if needed')],
'T13-01':[L(0,1760,494,'High-resolution output'),L(4,1740,374,'4096 px long edge'),L(9,1680,620,'Tile size: 1536'),L(12,1830,620,'Context: 128 px')],
'T13-02':[E(0,960,192,'Final checks passed'),E(6,960,850,'Inspect each tile before acceptance'),R(11,1040,600,'Inspect the 4K result'),L(15,1740,285,'4096 × 2304 pixels')],
'T13-03':[E(0,920,680,'Download the finished image',click=True),E(3,1730,35,'Save board',click=True),E(13,1210,600,'Finished image · source retained')]
}
for c in rows:
 if c['id'] in shots:c['shots']=[dict(at=t,**s)for t,s in shots[c['id']]]
 if c['chapter']=='T10':
  for s in c['shots']:s['left']='export-layers-expanded';s['scroll']=830
 c['cursor']=events[c['id']]
 if c['id'] in ['T11-05','T12-04']:
  tracks=json.loads((F/'divider-tracks.json').read_text());c['shots'][0]['divider']=tracks['whole'if c['id']=='T11-05'else'local']
 # Content pans precede an offscreen target. Both the pixels and hotspot use
 # the same source offset, so a scroll never leaves a pointer on stale pixels.
 for e in c['cursor']:
  if e['space']!='body':continue
  s=max((s for s in c['shots']if s['at']<=e['at']),key=lambda s:s['at'])
  y=s.get('scroll',0)
  for p in s.get('pan',[]):
   if p[0]<=e['at']-s['at']:y=p[1]
  if e['y']-y<55 or e['y']-y>685:
   s.setdefault('pan',[]).append([max(0,e['at']-s['at']-.7),max(0,min(1078,e['y']-350))]);s['pan'].sort()
 # Start each cue with a cursor; it remains parked after the last guided action.
 if c['cursor'][0]['at']>0:c['cursor'].insert(0,{**c['cursor'][0],'at':0,'click':False})
 c['title']=next(x['title']for x in json.loads((M/'production/tutorial-v01/script.json').read_text(encoding='utf8'))['chapters']if x['id']==c['chapter'])
for f in F.glob('web-*.png'):shutil.copy2(f,P/f.name)
(O/'timeline.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
jsx=["import React from 'react';","import {AbsoluteFill,Sequence,Audio,staticFile} from 'remotion';","import {TutorialSceneV02} from './TutorialFullSceneV02';","import {BasicCaptions} from './basic-captions.element';",f"export const tutorialV02Frames={rows[-1]['start']+rows[-1]['frames']};","export const TutorialFullV02:React.FC=()=> <AbsoluteFill style={{background:'#10251d'}}>" ]
for c in rows:
 props={k:c[k]for k in ['id','chapter','title','shots','cursor']}
 jsx += [f'<Sequence name={json.dumps(c["id"]+" · "+c["title"])} from={{{c["start"]}}} durationInFrames={{{c["frames"]}}}>','<TutorialSceneV02 {...'+json.dumps(props,ensure_ascii=False)+'}/>',f'<Sequence from={{21}} layout="none"><Audio src={{staticFile("case/tutorial-full-v01/{c["id"]}.wav")}} /></Sequence>','<div style={{position:"absolute",left:310,bottom:22,transform:"scale(.53)",transformOrigin:"bottom left"}}><BasicCaptions name="English subtitles" width={2450} combineTokensWithinMilliseconds={0} captions={'+json.dumps(c['captions'],ensure_ascii=False)+'}/></div>','</Sequence>']
jsx.append('</AbsoluteFill>;');(M/'src/TutorialFullV02.tsx').write_text('\n'.join(jsx),encoding='utf8')
print('Revised',len(rows),'cues; approved audio unchanged')

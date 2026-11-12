"""Assemble a local review from verified software outputs; no image fabrication."""
from pathlib import Path
import json, hashlib, shutil, html
from PIL import Image

VIDEO=Path(__file__).resolve().parents[1]
ROOT=VIDEO.parents[1]
SOURCE=ROOT/'artifacts/promo-production-20261112'
OUT=VIDEO/'out/workflow-keyframes-v02'
PUBLIC=VIDEO/'public/case/promo-20261112'
OUT.mkdir(parents=True,exist_ok=True)
session=json.loads((SOURCE/'web/session.json').read_text())
for key,value in session['generated'].items():
    if value.get('status')=='completed':
        shutil.copyfile(value['export']['path'],PUBLIC/'ai'/f'{key}.png')
for key,name in [('annotation','monet-local-edit'),('hd','monet-4k')]:
    item=session.get(key,{})
    if item.get('status')=='completed' and item.get('export'):
        shutil.copyfile(item['export']['path'],PUBLIC/'ai'/f'{name}.png')
        shutil.copyfile(item['export']['path'],SOURCE/'AI'/f'{name}.png')

frames=[]
for p in sorted(OUT.glob('[0-9][0-9]-*.png')):
    with Image.open(p) as im:
        assert im.size==(3840,2160),p
    frames.append(dict(file=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
assets=json.loads((SOURCE/'asset-manifest.json').read_text())
native=list(PUBLIC.glob('*/*.png'))
manifest=dict(keyframes=frames,nativeFrameCount=len([p for p in native if p.parent.name not in ('psd','ai')]),
              assetFiles=sum(len(a['files']) for a in assets),psdCount=3,
              board=session['board'],styles={k:v['status'] for k,v in session['generated'].items()},
              localEdit=session.get('annotation',{}).get('status'),hd=session.get('hd',{}).get('status'),
              disclaimer='Layout/interaction concepts use actual software captures and generated outputs. Not a live UI recording or continuous orbit video.')
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')

def img(path,alt='',cls=''):
    q=html.escape(str(path).replace('\\','/'))
    return f'<a href="{q}" target="_blank"><img class="{cls}" loading="lazy" src="{q}" alt="{html.escape(alt)}"></a>'
def asset_path(path):return '../../public/case/promo-20261112/'+str(path).replace('\\','/')

parts=['''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,"><title>SceneFlow · Workflow captures v02</title>
<style>*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#101812;color:#eef3e6;font:16px/1.6 system-ui,sans-serif}main{max-width:1500px;margin:auto;padding:40px 34px 80px}h1{font-size:46px;line-height:1.05;letter-spacing:-2px}h2{font-size:30px;margin:60px 0 20px;letter-spacing:-1px}h3{font-size:20px}p,small{color:#a9b9a0}a{color:#d9ff79;text-decoration:none}nav{display:flex;flex-wrap:wrap;gap:22px;border-bottom:1px solid #39482f;padding:18px 0 25px}img{display:block;width:100%;object-fit:contain;background:#f4f5ef}figure{margin:0}figcaption{padding:12px 14px;color:#b9caaa}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px}.thumbs{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}.card{border:1px solid #39482f;border-radius:10px;overflow:hidden;background:#19221a}.card img{aspect-ratio:16/9}.controls{display:flex;gap:18px;align-items:center;margin:20px 0}select,input{background:#24331f;color:#eaf1df;border:1px solid #4c613c;border-radius:6px;padding:9px 12px;font:inherit}input[type=range]{width:360px}details{border:1px solid #39482f;padding:18px;border-radius:10px;margin-top:18px}summary{cursor:pointer;font-size:23px}.botany{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin-top:20px}.botany img{height:240px;object-fit:contain;background-color:#e7eade;background-image:linear-gradient(45deg,#d9dfcf 25%,transparent 25%),linear-gradient(-45deg,#d9dfcf 25%,transparent 25%),linear-gradient(45deg,transparent 75%,#d9dfcf 75%),linear-gradient(-45deg,transparent 75%,#d9dfcf 75%);background-size:24px 24px;background-position:0 0,0 12px,12px -12px,-12px 0}.botany .plan{height:170px}.stats{display:flex;gap:30px;flex-wrap:wrap;color:#d9ff79;font-size:21px}.note{border-left:3px solid #d9ff79;padding-left:18px}code{color:#c9d7bb;overflow-wrap:anywhere}footer{margin-top:60px;border-top:1px solid #39482f;padding-top:24px}@media(max-width:800px){main{padding:26px 18px}.grid,.thumbs,.botany{grid-template-columns:1fr 1fr}h1{font-size:34px}.controls{flex-wrap:wrap}input[type=range]{max-width:100%}}</style><main>
<h1>SceneFlow / Workflow captures</h1><p>v02 · Actual Rhino B + SceneFlow outputs · English promotional workflow study</p>
<nav><a href="#keyframes">Keyframes</a><a href="#seasons">Seasons</a><a href="#orbit">Orbit poses</a><a href="#plants">Plant assets</a><a href="#materials">Materials</a><a href="#ai">AI outputs</a></nav>''']
parts.append(f'<div class="stats"><span>{manifest["nativeFrameCount"]} native frames</span><span>{manifest["assetFiles"]} asset PNGs</span><span>3 layered PSDs</span><span>3 AI styles</span></div>')
parts.append('<h2 id="keyframes">Interaction → transformation</h2><p>The layouts below are interaction concepts using actual output images. Click a frame to inspect its 4K PNG.</p><div class="grid">')
for f in frames:parts.append('<figure class="card">'+img(f['file'],f['file'])+'<figcaption>'+html.escape(Path(f['file']).stem.replace('-',' / ',1))+'</figcaption></figure>')
parts.append('</div><h2 id="seasons">Same camera. Different season.</h2><div class="controls"><label>Season <select id="season"><option value="planted-summer">Summer</option><option value="season-spring">Spring</option><option value="season-autumn">Autumn</option><option value="season-winter">Winter</option></select></label><label>Camera <select id="camera"><option value="Promo-Axon">Axon</option><option value="Promo-Human">Human</option><option value="Promo-Top">Top</option></select></label></div>')
parts.append('<img id="season-photo" src="'+asset_path('planted-summer/Promo-Axon.png')+'" alt="Native seasonal comparison"><p>Native captures use the same saved camera, sun, layout and shared physical-size assets. Top views use crown plans; human views use elevations.</p>')
parts.append('<h2 id="orbit">Actual orbit key poses</h2><div class="controls"><input id="orbit-range" type="range" min="0" max="7" step="1" value="0" aria-label="Orbit pose"><strong id="orbit-label">Pose 1 / 8</strong></div><img id="orbit-photo" src="'+asset_path('planted-summer/Promo-Orbit-00.png')+'" alt="Actual orbit pose"><p>Eight camera locations around the real Rhino model. These are key poses, not a continuous flight recording.</p>')
parts.append('<h2 id="plants">One species record. Four seasons. Two views.</h2>')
for a in assets:
    if not a['plant']:continue
    label='Betula nigra / River birch' if a['label']=='river-birch' else 'Acer rubrum / Red maple'
    byslot={f['slot']:f['file'] for f in a['files']}
    parts.append('<details open><summary>'+label+'</summary><div class="botany">')
    for season in ['spring','summer','autumn','winter']:
        v=a['variants'][season]
        parts.append('<figure class="card">'+img(asset_path(byslot[v['elevation']]),season+' elevation')+img(asset_path(byslot[v['plan']]),season+' crown plan','plan')+'<figcaption>'+season.capitalize()+' / elevation + plan</figcaption></figure>')
    parts.append('</div></details>')
parts.append('<p>All plant PNGs have real transparent alpha. Botanical identities and sources remain in each asset record. Appearance still needs artistic review; seasonal silhouettes are not guaranteed to match pixel-for-pixel.</p>')
parts.append('<h2 id="materials">Material alternatives</h2><div class="grid">')
for key in ['cedar','terracotta','limestone','brick']:
    p=asset_path('materials-'+key+'/Promo-Human.png')
    parts.append('<figure class="card">'+img(p,key)+'<figcaption>'+key.capitalize()+' / actual application</figcaption></figure>')
parts.append('</div><details><summary>New terracotta + seasonal ground textures</summary><div class="thumbs">')
for a in assets:
    if a['plant']:continue
    for f in a['files']:parts.append('<figure class="card">'+img(asset_path(f['file']),f['slot'])+'<figcaption>'+a['label']+' / '+f['slot']+'</figcaption></figure>')
parts.append('</div></details><h2 id="ai">Actual Web Studio generations</h2><div class="grid">')
for key in ['monet','starry-night','animated-film']:
    parts.append('<figure class="card">'+img(asset_path('ai/'+key+'.png'),key)+'<figcaption>'+key+'</figcaption></figure>')
if session.get('annotation',{}).get('status')=='completed':
    parts.append('<figure class="card">'+img(asset_path('ai/monet-local-edit.png'),'Actual local edit')+'<figcaption>Annotated facade edit / protected pixels outside the mask remain unchanged</figcaption></figure>')
parts.append('</div>')
if session.get('hd',{}).get('status')=='completed' and (PUBLIC/'ai/monet-4k.png').exists():
    parts.append('<h2>4K refinement</h2>'+img(asset_path('ai/monet-4k.png'),'Actual 4K refinement')+'<p>4096 × 2304. Click to inspect the exported full-resolution PNG.</p>')
else:parts.append('<p class="note">4K refinement is '+html.escape(str(session.get('hd',{}).get('status','not started')))+'. This page does not label an unfinished or review-required result as final.</p>')
parts.append('''<footer><p>Original inputs, child relationships, settings, descriptions and annotations are retained in the owned Web Studio board. No source model or old board was overwritten.</p><a href="../../production/Workflow-Capture-v02.md">Capture notes, limitations and file locations →</a></footer>
<script>const base='../../public/case/promo-20261112/';function updateSeason(){document.querySelector('#season-photo').src=base+document.querySelector('#season').value+'/'+document.querySelector('#camera').value+'.png';}document.querySelector('#season').onchange=updateSeason;document.querySelector('#camera').onchange=updateSeason;document.querySelector('#orbit-range').oninput=e=>{const n=Number(e.target.value);document.querySelector('#orbit-photo').src=base+'planted-summer/Promo-Orbit-'+String(n).padStart(2,'0')+'.png';document.querySelector('#orbit-label').textContent='Pose '+(n+1)+' / 8';};</script></main></html>''')
(OUT/'review.html').write_text('\n'.join(parts),encoding='utf-8')
print(json.dumps(manifest,indent=2))

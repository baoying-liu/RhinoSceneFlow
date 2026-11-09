"""File-only PhotoCraft contract: ordinary appearance and ID-addressed instructions.

Reserved containers are validated on return. Pixel edits to an instruction return
as a raster instruction, never guessed back into editable vector/text geometry.
"""
import copy, math, re
from pathlib import Path
from PIL import Image, ImageDraw
from psd_tools import PSDImage
from psd_tools.api.layers import Group, PixelLayer
from project import read_json, write_json

ROOT='SceneFlow Instructions [SF1]'
KINDS=('pen','arrow','text','label','edit','protect','reference')
TOKEN=re.compile(r'^\[SF:(pen|arrow|text|label|edit|protect|reference):([a-f0-9]{32})\]')

def leaf_image(layer, size):
    """Render the isolated layer, ignoring its eye; never ignore its opacity/mask."""
    return layer.composite(viewport=(0,0,*size),force=True,layer_filter=lambda _:True).convert('RGBA')

def seed(folder):
    from board_render import opened, font
    spec=read_json(folder/'editor.json');layout=spec['layout'];size=(layout['width'],layout['height']);scale=layout['scale'];ox,oy=layout['offset']
    psd=PSDImage.new('RGBA',size);previous=spec.get('previous')
    if previous:
        old=PSDImage.open(previous);before=spec.get('previousLayout') or dict(offset=[0,0])
        dx,dy=ox-before['offset'][0],oy-before['offset'][1]
        for layer in list(old):
            if layer.name==ROOT:continue
            if layer.is_group():
                for child in layer.descendants():
                    if not child.is_group():child.offset=(child.left+dx,child.top+dy)
            else:layer.offset=(layer.left+dx,layer.top+dy)
            layer.move_to_group(psd)
    else:
        source=PixelLayer.frompil(opened(spec['image']),psd,'Original · reference only',top=oy,left=ox);source.lock();psd.append(source)
        psd.append(PixelLayer.frompil(Image.new('RGBA',(1,1)),psd,'Appearance edits',top=oy,left=ox))
    root=Group.new(ROOT,parent=psd);root.visible=spec.get('specialVisible',True);groups={k:Group.new('SF · '+k,parent=root) for k in KINDS};entries=[]
    for item in spec['items']:
        item=copy.deepcopy(item);a=item.get('annotation');im=Image.new('RGBA',size);d=ImageDraw.Draw(im)
        def xy(x,y):return (x*scale+ox,y*scale+oy)
        if item['kind']=='reference':
            q=item['pose'];picture=opened(item['path']).resize((max(1,round(q['width']*scale)),max(1,round(q['height']*scale))),Image.Resampling.LANCZOS);im.alpha_composite(picture,tuple(round(v) for v in xy(q['x'],q['y'])))
        elif a.get('raster'):
            q=a['rasterPose'];picture=opened(item['path']).resize((max(1,round(q['width']*scale)),max(1,round(q['height']*scale))),Image.Resampling.LANCZOS);im.alpha_composite(picture,tuple(round(v) for v in xy(q['x'],q['y'])))
        else:
            pts=[xy(q[0],q[1]) for q in a.get('points',[])];width=max(1,round(a['size']*scale));color=a['color']
            if a['kind'] in ('text','label'):
                pos=xy(a['x'],a['y']);ft=font(a['size']*scale)
                if a['kind']=='label':
                    b=d.multiline_textbbox(pos,a.get('text',''),font=ft);d.rectangle((b[0]-4,b[1]-3,b[2]+4,b[3]+3),fill='#20382b',outline=color)
                d.multiline_text(pos,a.get('text',''),font=ft,fill=color)
            elif pts:
                if a['kind'] in ('edit','protect') and a.get('closed') and len(pts)>=3:d.polygon(pts,fill=color)
                elif len(pts)>1:d.line(pts,fill=color,width=width,joint='curve')
                else:
                    x,y=pts[0];d.ellipse((x-width/2,y-width/2,x+width/2,y+width/2),fill=color)
                if a['kind']=='arrow' and len(pts)>1:
                    x,y=pts[-1];angle=math.atan2(y-pts[-2][1],x-pts[-2][0]);r=max(12,width*4);d.polygon([(x,y),(x-r*math.cos(angle-.5),y-r*math.sin(angle-.5)),(x-r*math.cos(angle+.5),y-r*math.sin(angle+.5))],fill=color)
        box=im.getbbox() or (0,0,1,1);name=f"[SF:{item['kind']}:{item['id']}] "+item.get('name',item['kind'])[:80]
        layer=PixelLayer.frompil(im.crop(box),psd,name,top=box[1],left=box[0]);groups[item['kind']].append(layer)
        layer.visible=item.get('visible',True)
        im.save(folder/('seed-'+item['id']+'.png'));entries.append({k:v for k,v in item.items() if k!='path'})
    # PhotoCraft selects the top layer on open: leave an ordinary paint layer on top,
    # not a system folder (otherwise a new paint layer would enter that folder).
    psd.remove(root);psd.insert(max(0,len(psd)-1),root)
    psd.save(folder/'reference.psd')
    # Compare like-for-like decoded PSD pixels, including PSD colour/alpha rounding.
    canonical=PSDImage.open(folder/'reference.psd')
    for layer in canonical.descendants():
        match=TOKEN.match(layer.name)
        if match:leaf_image(layer,size).save(folder/('seed-'+match[2]+'.png'))
    write_json(folder/'layers-manifest.json',dict(schema=1,layout=layout,items=entries))

def read(folder,psd):
    """Never fall back to the all-layer compatibility image for an SF project."""
    m=read_json(folder/'layers-manifest.json');layout=m['layout'];size=(layout['width'],layout['height'])
    if psd.size!=size:raise ValueError('Keep the PhotoCraft canvas size unchanged; reopen after changing the consideration frame')
    roots=[l for l in psd if l.name==ROOT]
    if len(roots)!=1 or not roots[0].is_group():raise ValueError('SceneFlow instruction folder is missing or duplicated. Undo the deletion/rename before applying.')
    root=roots[0];groups={}
    for k in KINDS:
        found=[g for g in root if g.name=='SF · '+k and g.is_group()]
        if len(found)!=1:raise ValueError('Keep all SF instruction category folders; undo their deletion/rename')
        groups[k]=found[0]
    expected={a['id']:a for a in m['items']};found={};returned=[]
    allowed={id(root),*(id(g) for g in groups.values())}
    for layer in root.descendants():
        if id(layer) in allowed:continue
        match=TOKEN.match(layer.name)
        if not match or layer.is_group():raise ValueError('Create ordinary layers outside the SceneFlow folder; special layers must retain their [SF:...] ID')
        kind,ident=match.groups()
        if ident in found or ident not in expected or expected[ident]['kind']!=kind or layer.parent is not groups[kind]:raise ValueError('Duplicated, moved or unknown SceneFlow layer ID; undo before applying')
        found[ident]=layer
        if layer.blend_mode.value!=b'norm' or layer.has_effects():raise ValueError('Use Normal blend without effects for special instruction layers')
        im=leaf_image(layer,size);im.save(folder/('returned-'+ident+'.png'))
        before=Image.open(folder/('seed-'+ident+'.png')).convert('RGBA')
        import numpy as np
        changed=not np.array_equal(np.asarray(im),np.asarray(before));box=im.getbbox()
        # Read local eye only; hidden instructions remain available to AI independently.
        visible=bool(layer.visible and groups[kind].visible)
        entry=dict(id=ident,kind=kind,visible=visible,changed=changed,deleted=False)
        if box:
            crop=im.crop(box);crop.save(folder/('layer-'+ident+'.png'));entry.update(file='layer-'+ident+'.png',pose=dict(x=(box[0]-layout['offset'][0])/layout['scale'],y=(box[1]-layout['offset'][1])/layout['scale'],width=(box[2]-box[0])/layout['scale'],height=(box[3]-box[1])/layout['scale']))
            if kind=='reference' and changed:
                normalized=crop.resize(tuple(expected[ident]['originalSize']),Image.Resampling.LANCZOS);normalized.save(folder/('reference-'+ident+'.png'))
                project=PSDImage.new('RGBA',normalized.size);project.append(PixelLayer.frompil(normalized,project,'Appearance edits'));project.save(folder/('reference-'+ident+'.psd'))
        elif changed:entry['deleted']=True
        returned.append(entry)
    returned.extend(dict(id=a['id'],kind=a['kind'],deleted=True,changed=True) for a in m['items'] if a['id'] not in found)
    for container in (root,*groups.values()):
        if container.opacity!=255 or container.has_mask() or container.has_effects():raise ValueError('Keep SF folder opacity at 100%, without masks or effects; edit individual instruction layers')
    for layer in psd.descendants():
        if layer is root or any(p is root for p in parents(layer)):continue
        if layer.is_visible() and (layer.has_effects() or layer.clipping_layer or layer.kind=='adjustment' or layer.blend_mode.value not in (b'norm',b'pass',b'mul ',b'scrn',b'over',b'dark',b'lite')):
            raise ValueError('Appearance return supports pixel/text layers, masks and Normal/Multiply/Screen/Overlay/Darken/Lighten blends. Rasterize effects/adjustments or clipping groups before applying.')
    # Independent appearance declaration excludes special layers, including hidden ones.
    ordinary=psd.composite(viewport=(0,0,*size),force=True,ignore_preview=True,layer_filter=lambda l:l.is_visible() and l is not root and not any(p is root for p in parents(l)))
    ox,oy=layout['offset'];w,h=layout['imageSize'];ordinary=ordinary.convert('RGBA').crop((ox,oy,ox+w,oy+h));ordinary.save(folder/'image.png')
    small=ordinary.copy();small.thumbnail((1200,1200));small.save(folder/'preview.png')
    write_json(folder/'image.json',dict(width=w,height=h,layout=layout))
    write_json(folder/'layers-return.json',dict(schema=1,specialVisible=bool(root.visible),appearance=dict(excludesInstructions=True),instructions=returned))

def parents(layer):
    while layer.parent is not None:
        layer=layer.parent;yield layer

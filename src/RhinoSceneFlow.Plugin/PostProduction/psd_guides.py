"""PSD participation and independent, aligned model guides. File worker only."""
from pathlib import Path
import math
from PIL import Image, ImageDraw, ImageFont


KINDS = dict(depth=('Depth', 'White is near, black is far; empty background is not geometry.'),
             form=('Form', 'Massing, surface folds and silhouette; do not copy the white material.'),
             color=('Material regions', 'Categorical region boundaries, not requested surface colours.'),
             shadow=('Lighting', 'Sun direction and cast shadows, not additional objects.'),
             structure=('Structure', 'Aligned geometry guidance, not output appearance.'),
             reference=('Reference', 'Aligned layer appearance reference, not an extra output panel.'))


def kind(row, rows):
    lookup={r['id']:r for r in rows};seen=set();current=row
    while current and current['id'] not in seen:
        seen.add(current['id']);name=current['name'].lower()
        for key,words in (('depth',('depth','深度')),('form',('arctic','极地')),
                          ('color',('material color','material colour','材质颜色','材质色','color channel','colour channel')),
                          ('shadow',('shadow','阴影'))):
            if any(word in name for word in words):return key
        current=lookup.get(current.get('parent'))
    return None


def default_role(row, rows):
    guide=kind(row,rows)
    return ('reference' if guide=='shadow' else 'structure') if guide else row.get('role','generate')


def settings(rows, params):
    """Parent switches gate children; legacy role overrides remain meaningful."""
    enabled={};inherited={};result=[]
    for row in rows:
        active=params.get('layerParticipation',{}).get(row['id'],row.get('effectiveVisible',row.get('visible',True)))
        active=active and enabled.get(row.get('parent'),True)
        enabled[row['id']]=active
        role=params.get('roles',{}).get(row['id'],default_role(row,rows))
        role=inherited.get(row.get('parent')) or role
        inherited[row['id']]=role if role in ('preserve','exclude') else None
        guide=kind(row,rows)
        if params.get('roles',{}).get(row['id'])=='generate':guide=None
        result.append(dict(row,participates=active,role=role,guideKind=guide))
    return result


def mask_rows(rows):
    # Off means keep currently visible pixels, not remove the layer from the base.
    # Hidden guides never become visible in the source or the editable mask.
    return [dict(r,role=('preserve' if not r['participates'] else 'exclude' if r['role']=='exclude'
                         else 'generate' if r['role']=='structure' or r['guideKind'] and r['role']=='reference'
                         else r['role'])) for r in rows]


def prepare(folder, source, rows):
    """One bounded sheet, grouped by purpose; no additional model request."""
    from psd_tools import PSDImage
    psd=PSDImage.open(source);actual=[]
    def visit(container,parent=None):
        for layer in container:
            i=len(actual);row=rows[i] if i<len(rows) else None
            if row is None or row['name']!=layer.name or row['parent']!=parent:
                raise ValueError('PSD guide layers no longer match the source')
            actual.append((layer,row))
            if layer.is_group():visit(layer,row['id'])
    visit(psd)
    if len(actual)!=len(rows):raise ValueError('PSD guide layer count changed')
    groups={}
    for layer,row in actual:
        if layer.is_group() or not row['participates'] or row['role'] in ('preserve','exclude'):continue
        guide=row['guideKind'] or ('structure' if row['role']=='structure' else 'reference' if row['role']=='reference' or not row.get('effectiveVisible',True) else None)
        if guide:groups.setdefault(guide,[]).append((layer,row))
    if not groups:return []
    lookup={r['id']:(l,r) for l,r in actual};images=[];manifest=[]
    for guide,items in groups.items():
        allowed={r['id'] for l,r in items}
        for _,row in items:
            parent=row.get('parent')
            while parent:
                allowed.add(parent);parent=lookup[parent][1].get('parent')
        for layer,row in actual:
            # This is a private parsed copy; never save it back to the PSD.
            layer.visible=row['id'] in allowed
            if row['id'] not in allowed:continue
            if layer.blend_mode.value not in (b'norm',b'pass',b'mul '):raise ValueError('Unsupported guide blend: '+layer.name)
            if layer.is_group():
                if layer.opacity!=255 or layer.has_mask() or layer.has_vector_mask():raise ValueError('Simplify masked/transparent guide group: '+layer.name)
            elif layer.kind!='pixel' or layer.clipping_layer:raise ValueError('Rasterize/release clipping for guide: '+layer.name)
            if layer.has_effects():raise ValueError('Rasterize guide effects: '+layer.name)
        image=psd.composite(force=True,layer_filter=lambda l:l.visible)
        if image is None:continue
        # Use identical full-document bounds in every cell, including hidden guides.
        image=image.convert('RGBA');scale=min(720/image.width,620/image.height)
        image=image.resize((max(1,round(image.width*scale)),max(1,round(image.height*scale))),Image.Resampling.NEAREST if guide in ('depth','color') else Image.Resampling.LANCZOS)
        images.append(image);manifest.append(dict(kind=guide,title=KINDS[guide][0],instruction=KINDS[guide][1],layers=[dict(id=r['id'],name=r['name']) for _,r in items],width=psd.width,height=psd.height))
    if not images:return []
    columns=min(2,len(images));height=math.ceil(len(images)/columns)*768
    sheet=Image.new('RGB',(columns*768,height),'#edf1ec');draw=ImageDraw.Draw(sheet)
    path=Path('C:/Windows/Fonts/arial.ttf');font=ImageFont.truetype(str(path),24) if path.is_file() else ImageFont.load_default()
    for i,(image,item) in enumerate(zip(images,manifest)):
        x=i%columns*768;y=i//columns*768
        draw.text((x+24,y+18),str(i+1)+' - '+item['title'],font=font,fill='#203226')
        offset=(x+(768-image.width)//2,y+78+(620-image.height)//2)
        sheet.paste(image,offset,image.getchannel('A'));item.update(number=i+1,cell=[x,y,x+768,y+768],imageBounds=[*offset,offset[0]+image.width,offset[1]+image.height])
    sheet.save(folder/'psd-guides.png')
    return manifest

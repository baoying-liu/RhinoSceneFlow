"""Owned file-only raster worker for whole-image inputs, masks and exports."""
import json, sys, shutil, hashlib, math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from PIL import Image, ImageDraw, ImageOps, ImageFont
import numpy as np
from project import read_json, write_json
import canvas_context as context

Image.MAX_IMAGE_PIXELS=8192*8192

def opened(path):
    im=Image.open(path)
    if im.format not in ('PNG','JPEG','WEBP') or not 1<=im.width<=8192 or not 1<=im.height<=8192:raise ValueError('Supported: PNG/JPEG/WebP up to 8192 px per side')
    im.load();return ImageOps.exif_transpose(im).convert('RGBA')

def ingest(folder):
    im=opened(folder/'upload');im.save(folder/'image.png');im.thumbnail((1200,1200));im.save(folder/'preview.png')
    with Image.open(folder/'image.png') as full:write_json(folder/'image.json',dict(width=full.width,height=full.height))

def editor_seed(folder):
    from psd_tools import PSDImage
    from psd_tools.api.layers import PixelLayer
    im=opened(read_json(folder/'editor.json')['image'])
    psd=PSDImage.new('RGBA',im.size)
    psd.append(PixelLayer.frompil(im,psd,'Source reference'))
    psd.append(PixelLayer.frompil(Image.new('RGBA',im.size),psd,'Annotations'))
    psd.save(folder/'reference.psd')

def editor_read(folder):
    from psd_tools import PSDImage
    import struct
    with (folder/'upload.psd').open('rb') as f:header=f.read(26)
    if len(header)!=26:raise ValueError('Incomplete PSD header')
    magic,version,_,channels,h,w,depth,mode=struct.unpack('>4sH6sHIIHH',header)
    if magic!=b'8BPS' or version!=1:raise ValueError('Expected a PhotoCraft PSD project')
    if not 1<=w<=8192 or not 1<=h<=8192 or w*h>8192*8192:raise ValueError('Reference limit: 8192 pixels per side')
    psd=PSDImage.open(folder/'upload.psd')
    if not 1<=psd.width<=8192 or not 1<=psd.height<=8192 or psd.width*psd.height>8192*8192:
        raise ValueError('Reference limit: 8192 pixels per side')
    # PhotoCraft writes its own full-size compatibility composite. Do not reinterpret layers.
    if not psd.has_preview():raise ValueError('Save the PSD with Maximize Compatibility enabled')
    im=psd.topil()
    if im is None or im.size!=(psd.width,psd.height):raise ValueError('Save the PSD with its compatibility composite enabled')
    im=im.convert('RGBA');im.save(folder/'image.png')
    write_json(folder/'image.json',dict(width=im.width,height=im.height))
    im.thumbnail((1200,1200));im.save(folder/'preview.png')

def font(size):
    for p in ('C:/Windows/Fonts/msyh.ttc','C:/Windows/Fonts/arial.ttf'):
        if Path(p).is_file():return ImageFont.truetype(p,max(10,int(size)))
    return ImageFont.load_default()

def prepare(folder):
    s=read_json(folder/'snapshot.json');n=s['node'];im=opened(s['image']);w,h=im.size
    if s.get('parent') and n['params']['blend']<100:im=Image.blend(opened(s['parent']).resize(im.size,Image.Resampling.LANCZOS),im,n['params']['blend']/100)
    mask=Image.new('L',(w,h),255);p=n['params'];sx=w/n['pose']['width'];sy=h/n['pose']['height']
    if s.get('psd') and s.get('layers'):
        # Original PSD masks are used only on its source node, never reimposed on a generated child.
        from render import prepare as psd_prepare
        psdroot=folder/'psd';temp=psdroot/'runs'/'whole';temp.mkdir(parents=True,exist_ok=True);shutil.copyfile(s['psd'],psdroot/'source.psd')
        layers=[dict(l,role=p['roles'].get(l['id'],l.get('role','generate'))) for l in s['layers']]
        layers=[dict(l,role='generate' if l['role']=='structure' else l['role']) for l in layers]
        with Path(s['psd']).open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
        write_json(temp/'snapshot.json',dict(sourceSha256=digest,layers=layers,edgeGuard=int(p['edgeGuard']),tileSize=1024,tiles=[]))
        psd_prepare(temp);im=opened(temp/'base.png');mask=Image.open(temp/'edit-mask.png').convert('L')
    frame=n['frame'];fx,fy,fr,fb=frame['x'],frame['y'],frame['x']+frame['width'],frame['y']+frame['height']
    enabled=[]
    for a in n['annotations']:
        if not a.get('enabled',True):continue
        if context.area(context.bounds(a),dict(x=fx,y=fy,width=fr-fx,height=fb-fy))>0:enabled.append(a)
    local=Image.new('L',(w,h),0 if any(a['kind']=='edit' for a in enabled) else 255)
    markup=im.copy();draw=ImageDraw.Draw(markup);md=ImageDraw.Draw(local)
    notes=[]
    # Clip instructions to the selected frame before drawing; frame does not crop the output.
    clip=Image.new('L',(w,h),0);box=(max(0,int(fx*sx)),max(0,int(fy*sy)),min(w,int(fr*sx)),min(h,int(fb*sy)))
    if box[2]>box[0] and box[3]>box[1]:ImageDraw.Draw(clip).rectangle(box,fill=255)
    for a in enabled:
        pts=[(q[0]*sx,q[1]*sy) for q in a.get('points',[])];size=max(1,round(a.get('size',4)*sx));color=a.get('color','#e6a74b')
        if a['kind'] in ('edit','protect'):
            if a.get('closed') and len(pts)>=3:md.polygon(pts,fill=255 if a['kind']=='edit' else 0)
            elif len(pts)>1:md.line(pts,fill=255 if a['kind']=='edit' else 0,width=size,joint='curve')
            if pts:
                x,y=pts[-1];md.ellipse((x-size/2,y-size/2,x+size/2,y+size/2),fill=255 if a['kind']=='edit' else 0)
        elif a['kind'] in ('text','label'):
            notes.append(a.get('text',''));draw.text((a.get('x',0)*sx,a.get('y',0)*sy),a.get('text',''),fill=color,font=font(a['size']*sx))
        elif len(pts)>1:
            draw.line(pts,fill=color,width=size,joint='curve')
            if a['kind']=='arrow':
                x,y=pts[-1];angle=math.atan2(y-pts[-2][1],x-pts[-2][0]);r=max(12,size*4)
                draw.polygon([(x,y),(x-r*math.cos(angle-.5),y-r*math.sin(angle-.5)),(x-r*math.cos(angle+.5),y-r*math.sin(angle+.5))],fill=color)
    # Protect always wins regardless of annotation order.
    for a in enabled:
        if a['kind']=='protect':
            pts=[(q[0]*sx,q[1]*sy) for q in a.get('points',[])];size=max(1,round(a['size']*sx))
            if a.get('closed') and len(pts)>=3:md.polygon(pts,fill=0)
            elif len(pts)>1:md.line(pts,fill=0,width=size,joint='curve')
            if pts:
                x,y=pts[-1];md.ellipse((x-size/2,y-size/2,x+size/2,y+size/2),fill=0)
    arr=np.asarray(mask).astype(np.uint16)*np.asarray(local).astype(np.uint16)//255
    arr=arr*np.asarray(clip).astype(np.uint16)//255;arr[np.asarray(im)[:,:,3]==0]=0
    mask=Image.fromarray(arr.astype(np.uint8));mask.save(folder/'mask.png');im.save(folder/'base.png')
    markup=Image.composite(markup,im,clip)
    # A square letterbox gives deterministic coordinate backfill for arbitrary model output sizes.
    scale=1536/max(w,h);rw,rh=max(1,round(w*scale)),max(1,round(h*scale));ox,oy=(1536-rw)//2,(1536-rh)//2
    for name,image,bg in [('input',im,'white'),('markup',markup,'white'),('editable',mask,0)]:
        target=Image.new('RGB' if name!='editable' else 'L',(1536,1536),bg);small=image.resize((rw,rh),Image.Resampling.LANCZOS if name!='editable' else Image.Resampling.NEAREST)
        target.paste(small,(ox,oy),small.getchannel('A') if small.mode=='RGBA' else None);target.save(folder/(name+'.png'))
    spatial=context_diagram(folder,s,im,enabled)
    write_json(folder/'prepared.json',dict(spatial=spatial,width=w,height=h,offset=[ox,oy],size=[rw,rh],editablePixels=int(np.count_nonzero(arr)),totalPixels=w*h,notes=notes))
    for i,r in enumerate(s.get('references',[])):
        ref=opened(r['path']);clip=r['clip'];left=max(0,min(ref.width-1,math.floor(clip[0]*ref.width)));top=max(0,min(ref.height-1,math.floor(clip[1]*ref.height)))
        ref=ref.crop((left,top,max(left+1,min(ref.width,math.ceil(clip[2]*ref.width))),max(top+1,min(ref.height,math.ceil(clip[3]*ref.height)))))
        ref.thumbnail((1200,1200));ref.save(folder/('reference-'+str(i)+'.png'))
    references=s.get('references',[])
    if references:
        columns=min(2,len(references));rows=math.ceil(len(references)/columns)
        sheet=Image.new('RGB',(768*columns,768*rows),'#f4f5f2');sd=ImageDraw.Draw(sheet)
        for i,r in enumerate(references):
            ref=opened(folder/('reference-'+str(i)+'.png'));ref.thumbnail((720,660));x=(i%columns)*768;y=(i//columns)*768
            sheet.paste(ref,(x+(768-ref.width)//2,y+75+(660-ref.height)//2),ref.getchannel('A'))
            sd.text((x+25,y+20),str(i+1)+' · '+r['node']['params'].get('referencePurpose','general'),font=font(26),fill='#203226')
        sheet.save(folder/'reference-sheet.png')
    if not np.any(arr):raise ValueError('No editable pixels. Check layer roles, frame and protection strokes.')

def context_diagram(folder,s,im,marks):
    n=s['node'];f=n['frame'];p=n['pose'];scale=1472/max(f['width'],f['height']);ox=(1536-f['width']*scale)/2;oy=(1536-f['height']*scale)/2
    canvas=Image.new('RGBA',(1536,1536),'#edf1ec');d=ImageDraw.Draw(canvas);d.rectangle((ox,oy,ox+f['width']*scale,oy+f['height']*scale),fill='white')
    def xy(x,y):return ox+(x-f['x'])*scale,oy+(y-f['y'])*scale
    def paste(image,b):
        x=max(b['x'],f['x']);y=max(b['y'],f['y']);r=min(b['x']+b['width'],f['x']+f['width']);bottom=min(b['y']+b['height'],f['y']+f['height'])
        if r<=x or bottom<=y:return
        crop=image.crop((max(0,int((x-b['x'])/b['width']*image.width)),max(0,int((y-b['y'])/b['height']*image.height)),min(image.width,math.ceil((r-b['x'])/b['width']*image.width)),min(image.height,math.ceil((bottom-b['y'])/b['height']*image.height))))
        crop=crop.resize((max(1,round((r-x)*scale)),max(1,round((bottom-y)*scale))),Image.Resampling.LANCZOS);px,py=xy(x,y);canvas.paste(crop,(round(px),round(py)),crop.getchannel('A'))
    paste(im,dict(x=0,y=0,width=p['width'],height=p['height']))
    target=[*xy(0,0),*xy(p['width'],p['height'])];d.rectangle(target,outline='#5576a2',width=2);d.text(xy(0,0),'TARGET',fill='#254976',font=font(18))
    spatial=dict(frame=f,target=dict(x=0,y=0,width=1,height=1),annotations=[],references=[],legend='Coordinates normalized to target image. Negative/outside-1 positions are adjacent context. Arrow start/end links references or notes to intended subject regions.')
    for i,r in enumerate(s.get('references',[])):
        q=r.get('relativePose') or dict(x=r['node']['pose']['x']-p['x'],y=r['node']['pose']['y']-p['y'],width=r['node']['pose']['width'],height=r['node']['pose']['height'])
        paste(opened(r['path']),q);x,y=xy(max(q['x'],f['x']),max(q['y'],f['y']));d.text((x,y),'REF '+str(i+1),font=font(18),fill='#204eab')
        spatial['references'].append(dict(number=i+1,id=r['node']['id'],purpose=r['node']['params'].get('referencePurpose','general'),bounds={k:q[k]/p['width' if k in ('x','width') else 'height'] for k in q},crop=r['clip']))
    for a in marks:
        pts=[xy(q[0],q[1]) for q in a.get('points',[])];size=max(1,round(a['size']*scale));color=a['color'];b=context.bounds(a)
        item=dict(id=a['id'],kind=a['kind'],bounds={k:b[k]/p['width' if k in ('x','width') else 'height'] for k in b})
        if a['kind'] in ('text','label'):
            item['text']=a.get('text','');x,y=xy(a.get('x',0),a.get('y',0));ft=font(a['size']*scale)
            if a['kind']=='label':
                box=d.multiline_textbbox((x,y),item['text'],font=ft);d.rounded_rectangle((box[0]-5,box[1]-4,box[2]+5,box[3]+4),radius=4,fill='#24382c',outline=color)
            d.multiline_text((x,y),item['text'],font=ft,fill=color)
        elif pts:
            if a['kind'] in ('edit','protect') and a.get('closed'):
                tint='#69a78a' if a['kind']=='edit' else '#d47b82';d.line(pts+[pts[0]],fill=tint,width=2);item['closed']=True
            elif len(pts)>1:d.line(pts,fill=color,width=size,joint='curve')
            if a['kind']=='arrow' and len(pts)>1:
                x,y=pts[-1];angle=math.atan2(y-pts[-2][1],x-pts[-2][0]);r=max(10,size*3);d.polygon([(x,y),(x-r*math.cos(angle-.5),y-r*math.sin(angle-.5)),(x-r*math.cos(angle+.5),y-r*math.sin(angle+.5))],fill=color)
                item.update(start=[a['points'][0][0]/p['width'],a['points'][0][1]/p['height']],end=[a['points'][-1][0]/p['width'],a['points'][-1][1]/p['height']])
        spatial['annotations'].append(item)
    # Instructions outside the consideration frame must not leak into the model attachment.
    clip=Image.new('L',(1536,1536),0);ImageDraw.Draw(clip).rectangle((ox,oy,ox+f['width']*scale,oy+f['height']*scale),fill=255)
    clean=Image.new('RGBA',canvas.size,'#edf1ec');clean.paste(canvas,mask=clip);clean.convert('RGB').save(folder/'markup.png')
    return spatial

def finish(folder):
    s=read_json(folder/'snapshot.json');p=read_json(folder/'prepared.json');base=opened(folder/'base.png');raw=opened(folder/'generated.png')
    if raw.width*raw.height>16_777_216 or abs(raw.width/raw.height-1)>.025:raise ValueError('Expected a square letterboxed result; refused distorted backfill')
    generated=list(raw.size);raw=raw.resize((1536,1536),Image.Resampling.LANCZOS);x,y=p['offset'];w,h=p['size']
    candidate=raw.crop((x,y,x+w,y+h)).resize(base.size,Image.Resampling.LANCZOS)
    a=np.asarray(base);b=np.asarray(candidate);m=np.asarray(Image.open(folder/'mask.png')).astype(np.float32)/255
    rgb=np.clip(np.round(a[:,:,:3].astype(np.float32)*(1-m[:,:,None])+b[:,:,:3].astype(np.float32)*m[:,:,None]),0,255).astype(np.uint8)
    rgb[m==0]=a[:,:,:3][m==0];result=Image.fromarray(np.dstack([rgb,a[:,:,3]]));result.save(folder/'result.png')
    result.thumbnail((1200,1200));result.save(folder/'result-preview.png')
    write_json(folder/'result.json',dict(width=base.width,height=base.height,generatedSize=generated,
        editablePixels=p['editablePixels'],totalPixels=p['totalPixels'],changedPixels=int(np.count_nonzero(np.any(rgb!=a[:,:,:3],axis=2))),
        note='Mask/alpha restoration is exact. AI-added design details still require review.'))

def detail(folder):
    s=read_json(folder/'snapshot.json');im=opened(s['image']);size=s.get('descriptionSize',s['node']['params']['outputSize']);ratio=size/max(im.size)
    im=im.resize((max(1,round(im.width*ratio)),max(1,round(im.height*ratio))),Image.Resampling.LANCZOS)
    from psd_tools import PSDImage
    from psd_tools.api.layers import PixelLayer
    psd=PSDImage.new('RGBA',im.size);psd.append(PixelLayer.frompil(im,psd,'Approved whole-image anchor'));psd.save(folder/'detail.psd')

def export(folder):
    s=read_json(folder/'export.json');im=opened(s['image']);blend=s.get('blend',100)
    if blend<100 and s.get('parent'):
        parent=opened(s['parent']).resize(im.size,Image.Resampling.LANCZOS);im=Image.blend(parent,im,blend/100)
    fmt=s['format'];target=folder/('export.'+fmt)
    if fmt=='jpg':
        bg=Image.new('RGB',im.size,'white');bg.paste(im,mask=im.getchannel('A'));bg.save(target,quality=95,subsampling=0)
    else:im.save(target,format='PNG' if fmt=='png' else 'WEBP',**({'lossless':True} if fmt=='webp' else {}))

if __name__=='__main__':
    folder=Path(sys.argv[2]);{'ingest':ingest,'prepare':prepare,'finish':finish,'detail':detail,'export':export,'editor-seed':editor_seed,'editor-read':editor_read}[sys.argv[1]](folder)

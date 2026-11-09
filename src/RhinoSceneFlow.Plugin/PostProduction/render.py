"""Owned file-only raster worker: PSD masks, bounded crops, quality hints and PNG fusion."""
import hashlib
import json
import sys
from pathlib import Path
import cv2
import numpy as np
import pyvips
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parent))
from project import check_psd, write_json, read_json

pyvips.cache_set_max_mem(128 * 1024 * 1024)
pyvips.cache_set_max(100)


def vips(path):
    return pyvips.Image.new_from_file(str(path), access='random')


def array(image):
    image = image.cast('uchar')
    return np.frombuffer(image.write_to_memory(), dtype=np.uint8).reshape(image.height, image.width, image.bands).copy()


def crop(path, box):
    x,y,r,b = box
    return array(vips(path).crop(x,y,r-x,b-y))


def thumbnail(source, dest, size=1600):
    pyvips.Image.thumbnail(str(source), size, height=size, size='down').pngsave(str(dest))


def prepare(folder):
    folder = Path(folder)
    snapshot = read_json(folder/'snapshot.json')
    source = folder.parent.parent/'source.psd'
    check_psd(source)
    digest=hashlib.sha256()
    with source.open('rb') as stream:
        while chunk:=stream.read(1024*1024):digest.update(chunk)
    if digest.hexdigest()!=snapshot['sourceSha256']:
        raise ValueError('项目 PSD 快照已改变，拒绝使用旧计划。')
    from psd_tools import PSDImage
    psd = PSDImage.open(source)
    w,h = psd.width,psd.height
    rows = snapshot['layers']
    actual=[]
    def visit(container, parent=None, inherited=None):
        for layer in container:
            ident=str(len(actual)+1)
            row=next((r for r in rows if r['id']==ident), None)
            if row is None or row['name']!=layer.name or row['parent']!=parent:
                raise ValueError('PSD 图层与计划不匹配。')
            role=inherited or row['role']
            actual.append((layer,role))
            blend=layer.blend_mode.value
            if layer.is_visible() and role!='exclude':
                if blend not in (b'norm',b'pass',b'mul '):
                    raise ValueError('当前生图暂不支持此混合模式：'+layer.name)
                if layer.is_group():
                    if layer.opacity!=255 or layer.has_mask() or layer.has_vector_mask():
                        raise ValueError('请先简化带透明度/蒙版的分组：'+layer.name)
                elif layer.kind!='pixel' or layer.clipping_layer:
                    raise ValueError('当前生图需要普通像素图层，请先栅格化/释放剪贴层：'+layer.name)
            if layer.is_group():visit(layer, ident, role if role in ('preserve','exclude') else inherited)
    visit(psd)
    if len(actual)!=len(rows):raise ValueError('PSD 图层数量已改变。')
    roles={id(l):r for l,r in actual}
    base=psd.composite(force=True, layer_filter=lambda layer: layer.is_visible() and roles.get(id(layer))!='exclude')
    if base is None:raise ValueError('排除后没有可见图像。')
    base=base.convert('RGBA');base.save(folder/'base.png')
    editable=np.zeros((h,w),np.uint8)
    protected=np.zeros((h,w),np.uint8)
    transmittance=np.full((h,w),255,np.uint8)
    contours=np.zeros((h,w),np.uint8)
    for layer,role in reversed(actual):
        if layer.is_group() or not layer.is_visible() or role=='exclude':continue
        x,y,r,b=layer.bbox;x,y,r,b=max(0,x),max(0,y),min(w,r),min(h,b)
        if r<=x or b<=y:continue
        image=layer.composite(viewport=(x,y,r,b),force=True)
        if image is None:continue
        a=np.asarray(image.convert('RGBA'))[:,:,3].astype(np.uint16)
        t=transmittance[y:b,x:r].astype(np.uint16)
        visible=((t*a+127)//255).astype(np.uint8)
        if role=='generate':
            edit=editable[y:b,x:r].astype(np.uint16)+visible
            editable[y:b,x:r]=np.minimum(edit,255).astype(np.uint8)
            # Per-material boundaries survive even when two editable materials touch.
            boundary=cv2.morphologyEx((a>=128).astype(np.uint8)*255,cv2.MORPH_GRADIENT,np.ones((3,3),np.uint8),borderType=cv2.BORDER_CONSTANT,borderValue=0)
            boundary[visible==0]=0
            contours[y:b,x:r]=np.maximum(contours[y:b,x:r],boundary)
        elif role=='preserve':
            protected[y:b,x:r][visible>0]=255
        transmittance[y:b,x:r]=((t*(255-a)+127)//255).astype(np.uint8)
    source_alpha=np.asarray(base)[:,:,3]
    guard_contours=contours
    if snapshot.get('approvedAnchor'):
        # A flattened approved image has no semantic alpha boundaries. Diagnose
        # visible image edges instead of mistaking the white canvas border for a building.
        gray=cv2.cvtColor(np.asarray(base.convert('RGB')),cv2.COLOR_RGB2GRAY)
        contours=cv2.Canny(cv2.GaussianBlur(gray,(5,5),1),80,160)
        contours[:2,:]=0;contours[-2:,:]=0;contours[:,:2]=0;contours[:,-2:]=0
    editable[source_alpha==0]=0
    editable[protected>0]=0
    guard=int(snapshot.get('edgeGuard',1))
    if guard:
        # Visual Canny edges are diagnostic only. Pasting their old pixels into a
        # slightly shifted AI image creates double edges, not geometric protection.
        boundary=cv2.dilate(guard_contours,np.ones((guard*2+1,guard*2+1),np.uint8))
        editable[boundary>0]=0
    Image.fromarray(editable).save(folder/'edit-mask.png')
    Image.fromarray(protected).save(folder/'protected-mask.png')
    Image.fromarray(contours).save(folder/'structure.png')
    thumbnail(folder/'base.png',folder/'base-preview.png')
    thumbnail(folder/'edit-mask.png',folder/'mask-preview.png')
    # Global reference is letterboxed, never stretched into a square.
    global_image=base.copy();global_image.thumbnail((1536,1536))
    global_canvas=Image.new('RGB',(1536,1536),'white')
    global_canvas.paste(global_image,((1536-global_image.width)//2,(1536-global_image.height)//2),global_image.getchannel('A'))
    global_canvas.save(folder/'global-source.png')
    counts=[]
    size=snapshot['tileSize']
    for tile in snapshot['tiles']:
        core=tile['core'];x,y,r,b=tile['context']
        if snapshot.get('approvedAnchor'):size=max(r-x,b-y)
        count=int(np.count_nonzero(editable[core[1]:core[3],core[0]:core[2]]))
        counts.append(dict(id=tile['id'],editablePixels=count))
        if not count:continue
        directory=folder/('tile-'+str(tile['id']));directory.mkdir(exist_ok=True)
        offset=[(size-(r-x))//2,(size-(b-y))//2]
        rgba=Image.fromarray(crop(folder/'base.png',(x,y,r,b)))
        image=Image.new('RGB',(size,size),'white');image.paste(rgba,tuple(offset),rgba.getchannel('A'))
        image.save(directory/'input.png')
        mask=Image.new('L',(size,size),0);mask.paste(Image.fromarray(editable[y:b,x:r]),tuple(offset));mask.save(directory/'mask.png')
        outline=Image.new('L',(size,size),0);outline.paste(Image.fromarray(contours[y:b,x:r]),tuple(offset));outline.save(directory/'structure.png')
        write_json(directory/'placement.json',dict(offset=offset,width=r-x,height=b-y,size=size))
    write_json(folder/'prepared.json',dict(editablePixels=int(np.count_nonzero(editable)),protectedPixels=int(np.count_nonzero(protected)),tiles=counts))
    if not np.any(editable):raise ValueError('没有可修改的可见像素，请将需要处理的像素图层设为“可修改”。')


def quality(directory, candidate):
    directory=Path(directory)
    placement=read_json(directory/'placement.json')
    image=Image.open(candidate)
    original_size=list(image.size)
    if image.width*image.height>16_777_216 or abs(image.width/image.height-1)>.025:
        raise ValueError('AI 未返回要求的方形分块，拒绝拉伸回填；请重试。')
    image.load()
    size=placement['size'];image=image.convert('RGB').resize((size,size),Image.Resampling.LANCZOS)
    target=np.asarray(image)
    source=np.asarray(Image.open(directory/'input.png').convert('RGB'))
    structure=np.asarray(Image.open(directory/'structure.png').convert('L'))
    edge=cv2.Canny(cv2.cvtColor(target,cv2.COLOR_RGB2GRAY),60,140)
    distance=cv2.distanceTransform(255-edge,cv2.DIST_L2,3)
    values=distance[structure>0]
    p90=float(np.percentile(values,90)) if len(values)>=64 else None
    # A diagnostic hint, not a certificate of geometric accuracy.
    review=p90 is not None and p90>max(9,size*.018)
    delta=float(np.mean(np.abs(target.astype(np.float32)-source)))
    x,y=placement['offset'];w,h=placement['width'],placement['height']
    image.crop((x,y,x+w,y+h)).save(directory/'candidate.png')
    thumbnail(directory/'candidate.png',directory/'candidate-preview.png',768)
    return dict(generatedSize=original_size,normalizedSize=[size,size],edgeDistanceP90=p90,
                changedMean=delta,review=review,note='轮廓距离仅为检查提示；不能证明窗框、道路等所有结构正确。')


def feather(tile):
    x,y,r,b=tile['context'];cx,cy,cr,cb=tile['core']
    xx=np.arange(x,r);yy=np.arange(y,b)
    wx=np.ones(r-x,np.float32);wy=np.ones(b-y,np.float32)
    if cx>x:wx[xx<cx]=np.sin(np.pi/2*(xx[xx<cx]-x+.5)/(cx-x))**2
    if r>cr:wx[xx>=cr]=np.sin(np.pi/2*(r-xx[xx>=cr]-.5)/(r-cr))**2
    if cy>y:wy[yy<cy]=np.sin(np.pi/2*(yy[yy<cy]-y+.5)/(cy-y))**2
    if b>cb:wy[yy>=cb]=np.sin(np.pi/2*(b-yy[yy>=cb]-.5)/(b-cb))**2
    return np.maximum(1,np.round(wy[:,None]*wx[None,:]*255)).astype(np.uint8)


def offsets(folder, accepted):
    """Fit bounded RGB offsets from actual overlaps; zero-mean gauge preserves the overall palette."""
    rows=[];values=[]
    for i,a in enumerate(accepted):
        for j in range(i+1,len(accepted)):
            b=accepted[j];x=max(a['context'][0],b['context'][0]);y=max(a['context'][1],b['context'][1]);r=min(a['context'][2],b['context'][2]);bottom=min(a['context'][3],b['context'][3])
            if r-x<8 or bottom-y<8:continue
            aa=crop(folder/a['image'],(x-a['context'][0],y-a['context'][1],r-a['context'][0],bottom-a['context'][1]))[:,:,:3]
            bb=crop(folder/b['image'],(x-b['context'][0],y-b['context'][1],r-b['context'][0],bottom-b['context'][1]))[:,:,:3]
            mask=crop(folder/'edit-mask.png',(x,y,r,bottom))[:,:,0]>64
            if np.count_nonzero(mask)<64:continue
            aa=cv2.GaussianBlur(aa.astype(np.float32),(0,0),3);bb=cv2.GaussianBlur(bb.astype(np.float32),(0,0),3)
            difference=np.median((bb-aa)[mask],axis=0)
            row=np.zeros(len(accepted),np.float32);row[i]=1;row[j]=-1
            rows.append(row);values.append(difference)
    if not rows:return np.zeros((len(accepted),3),np.float32)
    rows.append(np.ones(len(accepted),np.float32));values.append(np.zeros(3,np.float32))
    return np.clip(np.linalg.lstsq(np.array(rows),np.array(values),rcond=None)[0],-24,24)


def compose(folder):
    folder=Path(folder);state=read_json(folder/'run.json')
    accepted=[t for t in state['tiles'] if t['status']=='completed' and t.get('image')]
    if not accepted:return dict(accepted=0,partial=True)
    base=vips(folder/'base.png');w,h=base.width,base.height
    corrections=offsets(folder,accepted) if state.get('colorMatch',True) else np.zeros((len(accepted),3))
    strips=[];strip_dir=folder/('fusion-'+state['fusionId']);strip_dir.mkdir(exist_ok=True)
    changed=0
    # Multi-band reconstruction is bounded to a strip with 64px pyramid halos.
    for top in range(0,h,384):
        bottom=min(h,top+384);sy=max(0,top-64);sb=min(h,bottom+64)
        source=array(base.crop(0,sy,w,sb-sy));rgb=source[:,:,:3]
        if source.shape[2]==3:source=np.dstack([source,np.full((sb-sy,w),255,np.uint8)])
        mask=crop(folder/'edit-mask.png',(0,sy,w,sb))[:,:,0]
        blender=cv2.detail_MultiBandBlender(0,4)
        blender.prepare((0,0,w,sb-sy))
        coverage=np.zeros((sb-sy,w),np.uint8)
        for index,tile in enumerate(accepted):
            x,y,r,b=tile['context'];ty=max(y,sy);tb=min(b,sb)
            if ty>=tb:continue
            piece=crop(folder/tile['image'],(0,ty-y,r-x,tb-y))[:,:,:3].astype(np.float32)+corrections[index]
            weight=feather(tile)[ty-y:tb-y,:]
            blender.feed(np.clip(np.round(piece),0,255).astype(np.int16),weight,(x,ty-sy))
            coverage[ty-sy:tb-sy,x:r]=np.maximum(coverage[ty-sy:tb-sy,x:r],weight)
        result,_=blender.blend(None,None) if np.any(coverage) else (rgb,None)
        alpha=mask.astype(np.float32)/255
        # Single-block trials fade to the unchanged source beyond their core.
        alpha*=coverage.astype(np.float32)/255
        mixed=np.clip(np.round(rgb.astype(np.float32)*(1-alpha[:,:,None])+result.astype(np.float32)*alpha[:,:,None]),0,255).astype(np.uint8)
        mixed[mask==0]=rgb[mask==0]  # byte-exact readonly/background restoration
        rgba=np.dstack([mixed,source[:,:,3]])
        out=rgba[top-sy:bottom-sy]
        changed+=int(np.count_nonzero(np.any(out[:,:,:3]!=source[top-sy:bottom-sy,:,:3],axis=2)))
        path=strip_dir/(str(top)+'.png');Image.fromarray(out).save(path);strips.append(path)
    result=vips(strips[0])
    for strip in strips[1:]:result=result.join(vips(strip),'vertical')
    target=folder/('result-'+state['fusionId']+'.png');result.pngsave(str(target))
    preview=folder/('result-'+state['fusionId']+'-preview.png');thumbnail(target,preview)
    report=dict(accepted=len(accepted),partial=any(t['status'] not in ('completed','skipped') for t in state['tiles']),
                image=target.name,preview=preview.name,changedPixels=changed,width=w,height=h,
                colorOffsets=corrections.tolist(),fusion='OpenCV multiband / overlap color offsets / exact protected pixels')
    write_json(folder/('fusion-'+state['fusionId']+'.json'),report)
    return report


if __name__=='__main__':
    operation=sys.argv[1];folder=Path(sys.argv[2])
    if operation=='prepare':prepare(folder)
    elif operation=='quality':write_json(folder/'quality.json',quality(folder,sys.argv[3]))
    elif operation=='compose':write_json(folder/'composed.json',compose(folder))
    else:raise ValueError('Unknown raster operation')

"""File-only PSD preparation. No Rhino objects or model execution in this process."""
import hashlib
import json
import math
import os
import struct
import time
import uuid
from pathlib import Path

MAX_BYTES = 2_000_000_000
MAX_PIXELS = 8192 * 8192


def read_json(path):
    for attempt in range(80):
        try:
            return json.loads(Path(path).read_text(encoding='utf-8'))
        except PermissionError:
            if attempt==79:raise
            time.sleep(.025)


def write_json(path, value):
    path = Path(path)
    # Do not repeat a long destination name: nested Windows run folders otherwise
    # push the temporary file past MAX_PATH even when the final JSON path is valid.
    temp = path.with_name('.'+uuid.uuid4().hex+'.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    try:
        # Windows readers and sync/indexing software can briefly deny rename.
        # Never fall back to truncating the live JSON or deleting the destination.
        for attempt in range(80):
            try:
                os.replace(temp, path)
                return
            except PermissionError:
                if attempt==79:raise
                time.sleep(.025)
    finally:
        temp.unlink(missing_ok=True)


def check_psd(path):
    path = Path(path)
    if path.suffix.lower() not in ('.psd', '.psb') or not path.is_file():
        raise ValueError('请选择现有的 PSD / PSB 文件。')
    if path.stat().st_size > MAX_BYTES:
        raise ValueError('第一版支持最大 2 GB 文件。')
    with path.open('rb') as stream:
        head = stream.read(26)
    if len(head) != 26 or head[:4] != b'8BPS':
        raise ValueError('文件不是有效的 Photoshop 文档。')
    _, version, _, channels, height, width, depth, mode = struct.unpack('>4sH6sHIIHH', head)
    if version not in (1, 2) or depth != 8 or mode != 3 or not 1 <= channels <= 56:
        raise ValueError('第一版支持 8-bit RGB PSD / PSB，请先转换颜色模式。')
    if not 1 <= width <= 8192 or not 1 <= height <= 8192 or width * height > MAX_PIXELS:
        raise ValueError('第一版图像边长上限为 8192 像素。')
    return width, height


def tiles(width, height, size, overlap):
    if size not in (512, 1024, 1536, 2048) or overlap not in (32, 64, 128, 256) or overlap * 2 >= size:
        raise ValueError('分块尺寸或上下文范围无效。')
    step = size - overlap * 2
    if math.ceil(width / step) * math.ceil(height / step) > 512:
        raise ValueError('分块超过 512 个，请增大分块尺寸。')
    result = []
    nx,ny=math.ceil(width/step),math.ceil(height/step)
    def window(center,extent,limit):
        extent=min(extent,limit);start=max(0,min(limit-extent,round(center-extent/2)))
        return start,start+extent
    # Balanced cores and inward-shifted context avoid tiny white-padded border tiles.
    for iy in range(ny):
        for ix in range(nx):
            x,r=round(ix*width/nx),round((ix+1)*width/nx)
            y,b=round(iy*height/ny),round((iy+1)*height/ny)
            core=[x,y,r,b]
            extent=min(size,max(r-x+2*overlap,b-y+2*overlap,round(size*.75)))
            left,right=window((x+r)/2,extent,width);top,bottom=window((y+b)/2,extent,height)
            context=[left,top,right,bottom]
            result.append(dict(id=len(result)+1, core=core, context=context, status='planned'))
    return result


def prepare(folder):
    from psd_tools import PSDImage
    folder = Path(folder)
    source = folder / 'source.psd'
    check_psd(source)
    psd = PSDImage.open(source)
    layers = []

    def visit(container, parent=None):
        # Photoshop/psd-tools traversal is bottom to top. Preserve that order in data.
        for layer in container:
            if len(layers) >= 256:
                raise ValueError('第一版最多支持 256 个图层 / 分组。')
            ident = str(len(layers)+1)
            group = layer.is_group()
            if layer.width > 8192 or layer.height > 8192 or layer.width * layer.height > MAX_PIXELS:
                raise ValueError('某图层的像素范围超过第一版 8192 上限，请裁切画布外的超大图层。')
            blend = layer.blend_mode.value.decode('ascii', errors='replace')
            row = dict(id=ident, parent=parent, name=layer.name, group=group,
                       visible=layer.visible, effectiveVisible=layer.is_visible(),
                       opacity=layer.opacity, blend=blend, bounds=list(layer.bbox),
                       role='reference' if group or not layer.is_visible() else 'generate')
            layers.append(row)
            if group:
                visit(layer, ident)
            elif layer.width and layer.height:
                image = layer.composite()
                if image:
                    image.thumbnail((192, 192))
                    image.save(folder / ('layer-'+ident+'.png'))
                    row['thumbnail'] = 'layer-'+ident+'.png'
    visit(psd)
    image = psd.composite()
    if image is None:
        raise ValueError('PSD 没有可合成的图像。')
    image.save(folder / 'composite.png')
    image.thumbnail((1600, 1600))
    image.save(folder / 'preview.png')
    digest = hashlib.sha256()
    with source.open('rb') as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    write_json(folder / 'document.json', dict(width=psd.width, height=psd.height,
               sha256=digest.hexdigest(), layers=layers,
               warning='预览由 psd-tools 合成；复杂调整层、智能对象和图层效果可能与 Photoshop 不同。'))


if __name__ == '__main__':
    import sys
    prepare(sys.argv[1])

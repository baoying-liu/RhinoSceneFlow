"""Independent final-output checks. Bounded previews; no image warping or model calls."""
import cv2
import numpy as np

def inspect(folder,target,tiles,read_crop,read_preview):
    import pyvips
    base=pyvips.Image.new_from_file(str(folder/'base.png'),access='random');w,h=base.width,base.height
    readonly=alpha=0
    for y in range(0,h,256):
        box=(0,y,w,min(y+256,h));a=read_crop(folder/'base.png',box);b=read_crop(target,box);mask=read_crop(folder/'edit-mask.png',box)[:,:,0]
        aa=a[:,:,3] if a.shape[2]>3 else np.full(a.shape[:2],255,np.uint8)
        alpha+=int(np.count_nonzero(aa!=b[:,:,3]));readonly+=int(np.count_nonzero(np.any(a[:,:,:3]!=b[:,:,:3],axis=2)&(mask==0)))
    scale=min(1,1600/max(w,h));size=(max(1,round(w*scale)),max(1,round(h*scale)))
    result=read_preview(target,*size)[:,:,:3];mask=read_preview(folder/'edit-mask.png',*size)[:,:,0]>64
    entries=[];supported=np.zeros(result.shape[:2],np.uint8)
    for t in tiles:
        x,y,r,b=t['context'];left,top,right,bottom=map(lambda v:round(v*scale),(x,y,r,b))
        im=read_preview(folder/t['image'],max(1,right-left),max(1,bottom-top))[:,:,:3]
        edge=cv2.Canny(cv2.cvtColor(im,cv2.COLOR_RGB2GRAY),60,140);edge=cv2.dilate(edge,np.ones((5,5),np.uint8))
        supported[top:bottom,left:right]=np.maximum(supported[top:bottom,left:right],edge)
        entries.append((left,top,right,bottom,im))
    seams=[]
    for axis,limit in [(0,w),(1,h)]:
        positions=set()
        for t in tiles:
            for box in ('core','context'):positions.update((t[box][axis],t[box][axis+2]))
        if axis==1:positions.update(range(384,h,384))
        for original in sorted(v for v in positions if 1<v<limit-1):
            p=round(original*scale)
            if p<1 or p>=(size[axis]-1):continue
            if axis==0:
                jump=np.mean(np.abs(result[:,p].astype(float)-result[:,p-1]),axis=1);expected=np.zeros(len(jump));covered=np.zeros(len(jump),bool);valid=mask[:,p]&mask[:,p-1]
            else:
                jump=np.mean(np.abs(result[p].astype(float)-result[p-1]),axis=1);expected=np.zeros(len(jump));covered=np.zeros(len(jump),bool);valid=mask[p]&mask[p-1]
            for l,t,r,b,im in entries:
                if axis==0 and l<p<r:
                    v=np.mean(np.abs(im[:,p-l].astype(float)-im[:,p-l-1]),axis=1);expected[t:b]=np.maximum(expected[t:b],v);covered[t:b]=True
                elif axis==1 and t<p<b:
                    v=np.mean(np.abs(im[p-t].astype(float)-im[p-t-1]),axis=1);expected[l:r]=np.maximum(expected[l:r],v);covered[l:r]=True
            valid&=covered
            excess=np.maximum(0,jump[valid]-expected[valid])
            if len(excess)>32:
                fraction=float(np.mean(excess>12));mean=float(np.mean(excess));flag=fraction>.08 and mean>5
                seams.append(dict(axis='x' if axis==0 else 'y',position=original,excessMean=mean,fraction=fraction,review=bool(flag)))
    blurred=[];textured=0
    gray=cv2.cvtColor(result,cv2.COLOR_RGB2GRAY)
    for y in range(0,size[1]-95,96):
        for x in range(0,size[0]-95,96):
            if np.mean(mask[y:y+96,x:x+96])<.8:continue
            variants=[cv2.Laplacian(cv2.cvtColor(im[y-t:y-t+96,x-l:x-l+96],cv2.COLOR_RGB2GRAY),cv2.CV_32F).var() for l,t,r,b,im in entries if l<=x and t<=y and r>=x+96 and b>=y+96]
            if not variants or np.median(variants)<40:continue
            textured+=1;ratio=float(cv2.Laplacian(gray[y:y+96,x:x+96],cv2.CV_32F).var()/np.median(variants))
            if ratio<.25:blurred.append(dict(x=round(x/scale),y=round(y/scale),ratio=ratio))
    edge=cv2.Canny(gray,60,140)>0;count=int(np.count_nonzero(edge&mask));unsupported=int(np.count_nonzero(edge&mask&(supported==0)));fraction=unsupported/max(1,count)
    reasons=[]
    if any(v['review'] for v in seams):reasons.append('seam')
    if len(blurred)>=3 and len(blurred)/max(1,textured)>.12:reasons.append('blur')
    if count>200 and fraction>.12:reasons.append('outlines')
    return dict(review=bool(reasons),reasons=reasons,readonlyChanged=readonly,alphaChanged=alpha,hardFailure=bool(readonly or alpha),seams=seams,blurredPatches=blurred[:20],texturedPatches=textured,unsupportedEdgeFraction=fraction,previewScale=scale)

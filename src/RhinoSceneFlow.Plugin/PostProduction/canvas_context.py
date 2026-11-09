"""Spatial canvas resources. Geometry is in board world units; frames choose context."""
import copy,json,hashlib

def frame(n):
 p=n['pose'];f=n['frame'];return dict(x=p['x']+f['x'],y=p['y']+f['y'],width=f['width'],height=f['height'])
def area(a,b):return max(0,min(a['x']+a['width'],b['x']+b['width'])-max(a['x'],b['x']))*max(0,min(a['y']+a['height'],b['y']+b['height'])-max(a['y'],b['y']))
def bounds(a):
 pts=a.get('points',[]);pad=a.get('size',5)/2
 if pts:return dict(x=min(p[0] for p in pts)-pad,y=min(p[1] for p in pts)-pad,width=max(p[0] for p in pts)-min(p[0] for p in pts)+pad*2,height=max(p[1] for p in pts)-min(p[1] for p in pts)+pad*2)
 lines=(a.get('text') or ' ').split('\n');size=a.get('size',16);pad=7 if a['kind']=='label' else 0
 return dict(x=a.get('x',0),y=a.get('y',0),width=max(sum(1 if ord(c)>255 else .65 for c in line) for line in lines)*size+pad*2+1,height=len(lines)*size+pad*2)
def translate(a,x,y):
 r=copy.deepcopy(a);r['x']=r.get('x',0)+x;r['y']=r.get('y',0)+y;r['points']=[[p[0]+x,p[1]+y,p[2]] for p in r.get('points',[])];return r
def alive(n):return not any(n.get(k) for k in ('deleted','hidden','archived'))
def owner(nodes,box):
 candidates=[(area(frame(n),box),n['id']) for n in nodes if n['kind']=='image' and alive(n)]
 candidates=[p for p in candidates if p[0]>0];return max(candidates,key=lambda p:(p[0],p[1]))[1] if candidates else None
def world_marks(b):
 result=[dict(annotation=copy.deepcopy(a),home=None) for a in b.get('marks',[]) if a.get('enabled',True)]
 for n in b['nodes']:
  if not alive(n):continue
  result.extend(dict(annotation=translate(a,n['pose']['x'],n['pose']['y']),home=n['id']) for a in n['annotations'] if a.get('enabled',True))
 return result
def collected(b,n):
 f=frame(n);p=n['pose'];marks=[];refs=[]
 for entry in world_marks(b):
  a=entry['annotation']
  if area(bounds(a),f)>0:marks.append(translate(a,-p['x'],-p['y']))
 for r in b['nodes']:
  if r['kind']=='reference' and alive(r) and area(r['pose'],f)>0:
   q=r['pose'];clip=[max(0,(f['x']-q['x'])/q['width']),max(0,(f['y']-q['y'])/q['height']),min(1,(f['x']+f['width']-q['x'])/q['width']),min(1,(f['y']+f['height']-q['y'])/q['height'])]
   resource=copy.deepcopy(r);edited=live_reference(r)
   if edited:resource.update(asset=edited['asset'],preview=edited['preview'],width=edited['width'],height=edited['height'])
   refs.append(dict(node=resource,clip=clip,relativePose=dict(x=q['x']-p['x'],y=q['y']-p['y'],width=q['width'],height=q['height'])))
 # An editing reference is guidance aligned to this image, never replacement source pixels.
 owner=n
 if not live_reference(owner):
  owner=next((x for x in b['nodes'] if x['id']==n.get('parentId')),None)
  while owner and owner.get('archived'):owner=next((x for x in b['nodes'] if x['id']==owner.get('parentId')),None)
 edited=live_reference(owner) if owner else None
 if n['kind']=='image' and edited:
  resource=dict(id=owner['id'],name=owner['name']+' · edited reference',asset=edited['asset'],preview=edited['preview'],width=edited['width'],height=edited['height'],params=dict(referencePurpose='edited-target'))
  refs.append(dict(node=resource,clip=[0,0,1,1],relativePose=dict(x=0,y=0,width=p['width'],height=p['height']),editingReference=True))
 return marks,refs

def live_reference(n):
 r=n.get('editReference') or {}
 return r if r.get('enabled',True) and r.get('sourceAsset')==n.get('asset') else None
def signature(b,n):
 marks,refs=collected(b,n)
 def rounded(v):
  if isinstance(v,float):return round(v,8)
  if isinstance(v,list):return [rounded(x) for x in v]
  if isinstance(v,dict):return {k:rounded(x) for k,x in v.items()}
  return v
 return hashlib.sha256(json.dumps(rounded(dict(frame=n['frame'],marks=marks,refs=[dict(id=r['node']['id'],asset=r['node']['asset'],purpose=r['node']['params'].get('referencePurpose','general'),pose=r['relativePose'],clip=r['clip']) for r in refs])),sort_keys=True).encode()).hexdigest()
def follow_marks(before,after,marks):
 old={n['id']:n for n in before};new={n['id']:n for n in after};result=[]
 for a in marks:
  target=owner(before,bounds(a));p=old.get(target);q=new.get(target)
  result.append(translate(a,q['pose']['x']-p['pose']['x'],q['pose']['y']-p['pose']['y']) if p and q else copy.deepcopy(a))
 return result

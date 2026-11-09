"""Frame-based deterministic tree layout. References travel with their owner."""
import copy
import canvas_context as context
GAP_X=140
GAP_Y=90

def box(n):
 p=n['pose'];f=n['frame'];return dict(x=p['x']+f['x'],y=p['y']+f['y'],width=f['width'],height=f['height'])
def overlap(a,b,gap=40):
 return a['x']<b['x']+b['width']+gap and b['x']<a['x']+a['width']+gap and a['y']<b['y']+b['height']+gap and b['y']<a['y']+a['height']+gap

def graph(nodes):
 images=[n for n in nodes if n['kind']=='image' and not any(n.get(k) for k in ('deleted','hidden','archived'))];ids={n['id']:n for n in nodes};live={n['id'] for n in images};parents={}
 for n in images:
  p=ids.get(n.get('parentId'));seen=set()
  while p and p['id'] not in live and p['id'] not in seen:seen.add(p['id']);p=ids.get(p.get('parentId'))
  parents[n['id']]=p['id'] if p and p['id'] in live else None
 return images,parents

def visible(nodes,collapsed=()):
 images,parents=graph(nodes);blocked=set(collapsed);byid={n['id']:n for n in images};result=[]
 for n in images:
  p=n;seen=set();hide=False
  while p:
   if p['id'] in blocked:hide=True;break
   if p['id'] in seen:hide=True;break
   seen.add(p['id']);p=byid.get(parents.get(p['id']))
  if not hide:result.append(n)
 return result,parents

def placements(nodes,positions):
 if any(abs(p[k])>1_000_000 for p in positions.values() for k in ('x','y')):raise ValueError('Layout exceeds canvas bounds; reduce oversized frames')
 old={n['id']:n for n in nodes};result=copy.deepcopy(nodes)
 for n in result:
  if n['id'] in positions:n['pose'].update(positions[n['id']])
  elif n['kind']=='reference':
   target=context.owner(nodes,n['pose'])
   if target in positions:
    owner=old[target];p=positions[target];n['pose']['x']+=p['x']-owner['pose']['x'];n['pose']['y']+=p['y']-owner['pose']['y']
 # Legacy marks keep world position outside frames; marks inside any frame follow that image.
 for n in result:
  previous=old[n['id']];dx=n['pose']['x']-previous['pose']['x'];dy=n['pose']['y']-previous['pose']['y'];updated=[]
  for a in previous.get('annotations',[]):
   world=context.translate(a,previous['pose']['x'],previous['pose']['y']);target=context.owner(nodes,context.bounds(world));delta=positions.get(target);base=old.get(target)
   ax=delta['x']-base['pose']['x'] if delta and base else 0;ay=delta['y']-base['pose']['y'] if delta and base else 0
   updated.append(context.translate(a,ax-dx,ay-dy))
  n['annotations']=updated
 return result

def arrange(nodes,collapsed=()):
 images,parents=visible(nodes,collapsed)
 if not images:return nodes
 live={n['id']:n for n in images};children={n['id']:[c for c in images if parents.get(c['id'])==n['id']] for n in images};roots=[n for n in images if parents.get(n['id']) not in live];depth={};heights={}
 stack=[(n,0,False) for n in reversed(roots)]
 while stack:
  n,d,done=stack.pop()
  if not done:
   depth[n['id']]=d;stack.append((n,d,True));stack.extend((c,d+1,False) for c in reversed(children[n['id']]))
  else:heights[n['id']]=max(n['frame']['height'],sum(heights[c['id']] for c in children[n['id']])+GAP_Y*max(0,len(children[n['id']])-1))
 widths={}
 for n in images:widths[depth[n['id']]]=max(widths.get(depth[n['id']],0),n['frame']['width'])
 columns={0:0}
 for d in range(1,max(widths)+1):columns[d]=columns[d-1]+widths[d-1]+GAP_X
 pos={}
 y=0;stack=[]
 for n in roots:stack.append((n,y));y+=heights[n['id']]+GAP_Y
 while stack:
  n,y=stack.pop();f=n['frame'];pos[n['id']]=dict(x=columns[depth[n['id']]]-f['x'],y=y+(heights[n['id']]-f['height'])/2-f['y']);total=sum(heights[c['id']] for c in children[n['id']])+GAP_Y*max(0,len(children[n['id']])-1);cy=y+(heights[n['id']]-total)/2
  for c in children[n['id']]:stack.append((c,cy));cy+=heights[c['id']]+GAP_Y
 return placements(nodes,pos)

def avoid(nodes,anchor,collapsed=()):
 images,_=visible(nodes,collapsed);fixed=next((n for n in images if n['id']==anchor),None)
 if not fixed:return nodes
 placed=[box(fixed)];pos={fixed['id']:dict(x=fixed['pose']['x'],y=fixed['pose']['y'])}
 for n in sorted((n for n in images if n['id']!=anchor),key=lambda n:(box(n)['y'],box(n)['x'],n['id'])):
  b=box(n)
  for _ in range(len(placed)+1):
   hits=[r for r in placed if overlap(b,r)]
   if not hits:break
   b['y']=max(r['y']+r['height']+GAP_Y for r in hits)
  pos[n['id']]=dict(x=b['x']-n['frame']['x'],y=b['y']-n['frame']['y']);placed.append(b)
 return placements(nodes,pos)

import canvas_context as context
"""Local, revisioned boards. Image identity is independent of list order and canvas pose."""
import copy, hashlib, json, math, os, re, shutil, time, uuid, zipfile
from pathlib import Path
from fastapi import HTTPException
from project import read_json, write_json
import board_layout as layout

ASSET = re.compile(r'^[a-f0-9]{64}(?:-preview)?\.(?:png|jpg|webp|psd)$')
PRESETS = {'faithful':(20,5), 'detail':(65,15), 'concept':(80,55)}
DEFAULTS = dict(generationStage='whole',editScope='auto',prompt='', preset='detail', detail=65, freedom=15, blend=100, edgeGuard=1,
                tileSize=1024, overlap=128, outputSize=2048, roles={},referencePurpose='general')

def ident(value):
    try:
        if uuid.UUID(value).hex != value: raise ValueError()
    except (ValueError, TypeError, AttributeError): raise ValueError('Invalid identifier')
    return value

def finite(value, lo=-1_000_000, hi=1_000_000):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not lo<=value<=hi:
        raise ValueError('Invalid numeric value')
    return value

def params(value):
    result={**DEFAULTS, **value}
    if set(result)-set(DEFAULTS):raise ValueError('Unknown generation parameter')
    if result['preset'] not in PRESETS or not isinstance(result['prompt'],str) or len(result['prompt'])>16000:raise ValueError('Invalid brief')
    if result['generationStage'] not in ('whole','detail'):raise ValueError('Invalid generation stage')
    if result['editScope'] not in ('auto','whole','local'):raise ValueError('Edit scope: whole | local')
    if result['referencePurpose'] not in ('general','style','material','form','plant','palette'):raise ValueError('Invalid reference purpose')
    for key in ('detail','freedom','blend'):finite(result[key],0,100)
    finite(result['edgeGuard'],0,3)
    if not isinstance(result['roles'],dict) or len(result['roles'])>256 or any(v not in ('generate','structure','preserve','reference','exclude') for v in result['roles'].values()):raise ValueError('Invalid layer roles')
    from project import tiles
    tiles(1,1,result['tileSize'],result['overlap'])
    if result['outputSize'] not in (1024,2048,4096):raise ValueError('Output size: 1024, 2048 or 4096')
    return result

def annotations(values):
    if not isinstance(values,list) or len(values)>1000:raise ValueError('Maximum 1000 annotations per image')
    result=[];total=0
    for value in values:
        a={k:v for k,v in value.items() if k in ('id','kind','points','x','y','text','color','size','enabled','visible','closed','raster','rasterPose')}
        ident(a['id'])
        if 'closed' in a and type(a['closed']) is not bool:raise ValueError('closed must be boolean')
        for k in ('visible','enabled'):
            if k in a and type(a[k]) is not bool:raise ValueError(k+' must be boolean')
        if a.get('raster'):
            if not ASSET.fullmatch(a['raster']) or not a['raster'].endswith('.png'):raise ValueError('Invalid annotation raster')
            q=a['rasterPose'];a['rasterPose']={k:finite(q[k],.001 if k in ('width','height') else -1_000_000) for k in ('x','y','width','height')}
        if a['kind'] not in ('pen','arrow','text','label','protect','edit'):raise ValueError('Unknown annotation tool')
        a['size']=finite(a.get('size',4),1,100)
        if not re.fullmatch(r'#[a-fA-F0-9]{6}',a.get('color','#e6a74b')):raise ValueError('Invalid annotation color')
        a.setdefault('color','#e6a74b');a.setdefault('enabled',True)
        for key in ('x','y'):a[key]=finite(a.get(key,0))
        if len(a.get('text',''))>2000:raise ValueError('Annotation text too long')
        points=a.get('points',[]);total+=len(points)
        if total>100_000:raise ValueError('Annotation point budget exceeded')
        for p in points:
            if len(p)!=3:raise ValueError('Expected x, y, pressure')
            finite(p[0]);finite(p[1]);finite(p[2],0,1)
        result.append(a)
    return result

class Store:
    def __init__(self,root):
        self.root=Path(root);self.boards=self.root/'boards';self.boards.mkdir(exist_ok=True)
    def folder(self,id):
        p=self.boards/ident(id)
        if not (p/'board.json').is_file():raise HTTPException(404,'Board not found')
        return p
    def read(self,id):
        value=read_json(self.folder(id)/'board.json')
        if value.get('schemaVersion')!=1:raise ValueError('Unsupported board format')
        self.migrate(value)
        h=self.edit_history(id);value['historyState']={k:len(h[k]) for k in ('undo','redo')}
        value.pop('editHistory',None)
        return value
    def fingerprint(self,b):
        n=[{k:v for k,v in n.items() if k not in ('busy','inputChanged')} for n in b['nodes']]
        return json.dumps(dict(name=b['name'],nodes=n,marks=b.get('marks',[]),collapsed=b['view'].get('collapsed',[]),canvasCollapsed=b['view'].get('canvasCollapsed',[])),sort_keys=True)
    def commit(self,value,record=True,before=None,barrier=False):
        if len(json.dumps(value,ensure_ascii=False).encode('utf-8'))>12_000_000:raise ValueError('Board metadata exceeds 12 MB; create another board')
        old=before if before is not None else self.read(value['id']);h=self.edit_history(value['id'])
        if value.get('marks',[])==old.get('marks',[]):value['marks']=context.follow_marks(old['nodes'],value['nodes'],value.get('marks',[]))
        previous={n['id']:n for n in old['nodes']}
        for n in value['nodes']:
            if n['kind']=='image' and n['id'] in previous and context.signature(old,previous[n['id']])!=context.signature(value,n):n['dirty']=True
        if barrier:h=dict(undo=[],redo=[])
        elif record and self.fingerprint(old)!=self.fingerprint(value):
            def clean(v):
                result={k:copy.deepcopy(x) for k,x in v.items() if k not in ('editHistory','historyState')}
                for n in result['nodes']:
                    n.pop('busy',None);n.pop('editReference',None)
                return result
            h['undo'].append(dict(before=clean(old),after=clean(value)));h['undo']=h['undo'][-30:];h['redo']=[]
        value['revision']+=1;value['updated']=time.time();value['historyState']={k:len(h[k]) for k in ('undo','redo')}
        # History is part of board.json publication so an interrupted write cannot split the edit and its undo.
        while len(json.dumps(h,ensure_ascii=False).encode('utf-8'))>24_000_000 and len(h['undo'])>1:h['undo'].pop(0)
        value['historyState']={k:len(h[k]) for k in ('undo','redo')}
        value['editHistory']=h
        while len(json.dumps(value,ensure_ascii=False).encode('utf-8'))>12_000_000 and (h['undo'] or h['redo']):
            stack=h['undo'] if h['undo'] else h['redo'];stack.pop(0)
        value['historyState']={k:len(h[k]) for k in ('undo','redo')}
        write_json(self.folder(value['id'])/'board.json',value)
        value.pop('editHistory',None)
        return value
    def edit_history(self,id):
        return read_json(self.folder(id)/'board.json').get('editHistory',dict(undo=[],redo=[]))
    def history(self,id,body):
        current=self.read(id)
        if current['revision']!=body.get('revision'):raise HTTPException(409,'Board changed; reload before undo')
        h=self.edit_history(id);direction=body.get('direction')
        if direction not in ('undo','redo'):raise ValueError('direction: undo | redo')
        if not h[direction]:return current
        command=h[direction].pop();target=copy.deepcopy(command['before' if direction=='undo' else 'after'])
        # The editor has one current slot, outside board undo and image version history.
        slots={n['id']:copy.deepcopy(n.get('editReference')) for n in current['nodes']}
        for n in target['nodes']:
            n.pop('editReference',None)
            if slots.get(n['id']):n['editReference']=slots[n['id']]
        other='redo' if direction=='undo' else 'undo';h[other].append(command)
        target['view']['camera']=current['view']['camera'];target['view']['mode']=current['view']['mode'];target['revision']=current['revision']+1;target['updated']=time.time()
        target['editHistory']=h;target['historyState']={k:len(h[k]) for k in ('undo','redo')};self.migrate(target)
        for n in target['nodes']:
            if n['kind']=='image' and context.signature(target,n)!=n.get('baseline',{}).get('contextSignature'):
                n['dirty']=True # Current reference slots are independent of the undone command.
        write_json(self.folder(id)/'board.json',target);target.pop('editHistory',None);return target
    def layout(self,id,body):
        b=self.read(id)
        if b['revision']!=body.get('revision'):raise HTTPException(409,'Board changed; reload layout')
        collapsed=b['view'].get('canvasCollapsed',[]);action=body.get('action','arrange')
        if action=='toggle':
            node=ident(body['node']);collapsed=list(collapsed)
            if node in collapsed:collapsed.remove(node)
            else:collapsed.append(node)
            b['view']['canvasCollapsed']=collapsed;b['nodes']=layout.arrange(b['nodes'],collapsed)
            visible={n['id'] for n in layout.visible(b['nodes'],collapsed)[0]};selected=b.get('selectedId')
            while selected and selected not in visible:
                current=next((n for n in b['nodes'] if n['id']==selected),None);selected=current.get('parentId') if current else None
            b['selectedId']=selected
        elif action=='reveal':
            node=ident(body['node']);current=next(n for n in b['nodes'] if n['id']==node)
            if current.get('deleted'):raise ValueError('Image was deleted')
            chain=set()
            while current:
                chain.add(current['id']);current=next((n for n in b['nodes'] if n['id']==current.get('parentId')),None)
            b['view']['canvasCollapsed']=[x for x in collapsed if x not in chain];b['selectedId']=node;b['nodes']=layout.arrange(b['nodes'],b['view']['canvasCollapsed'])
        elif action=='move':
            node=ident(body['node']);n=next(n for n in b['nodes'] if n['id']==node)
            if n.get('deleted'):raise ValueError('Image was deleted')
            positions={node:dict(x=finite(body['x']),y=finite(body['y']))};b['nodes']=layout.placements(b['nodes'],positions);b['nodes']=layout.avoid(b['nodes'],node,collapsed)
        elif action=='arrange':b['nodes']=layout.arrange(b['nodes'],collapsed)
        else:raise ValueError('Unknown layout action')
        return self.commit(b)
    def create(self,name='Untitled board',remember=True):
        if not isinstance(name,str) or not 0<len(name.strip())<=160:raise ValueError('Invalid board name')
        id=uuid.uuid4().hex;p=self.boards/id;p.mkdir();(p/'assets').mkdir();(p/'tasks').mkdir()
        b=dict(schemaVersion=1,id=id,name=name.strip(),revision=0,created=time.time(),updated=time.time(),nodes=[],marks=[],
               view=dict(mode='list',camera=dict(x=40,y=60,scale=.8)),selectedId=None)
        write_json(p/'board.json',b)
        if remember:self.preference(lastBoard=id)
        return b
    def preference(self,**patch):
        p=self.root/'board-preferences.json';v=read_json(p) if p.exists() else dict(language='auto',lastBoard=None)
        v.setdefault('backupLimit',2)
        if v.get('listWheelVersion')!=2:v['listWheel']='navigate';v['listWheelVersion']=2
        v.setdefault('listWheel','navigate');v.setdefault('autoLocate',True);v.setdefault('confirmDelete',True);v.setdefault('referenceAutoLocate',False)
        if 'referenceAutoLocate' in patch and type(patch['referenceAutoLocate']) is not bool:raise ValueError('referenceAutoLocate must be boolean')
        if 'confirmDelete' in patch and type(patch['confirmDelete']) is not bool:raise ValueError('confirmDelete must be boolean')
        if 'autoLocate' in patch and type(patch['autoLocate']) is not bool:raise ValueError('autoLocate must be boolean')
        if patch.get('listWheel',v['listWheel']) not in ('scroll','navigate'):raise ValueError('listWheel: scroll | navigate')
        if 'backupLimit' in patch and (type(patch['backupLimit']) is not int or not 0<=patch['backupLimit']<=100):raise ValueError('Backup limit: 0..100')
        if patch.get('language',v['language']) not in ('auto','zh-CN','en'):raise ValueError('Unknown language')
        v.update(patch)
        if patch:write_json(p,v)
        return v
    def asset(self,board,name):
        if not ASSET.fullmatch(name):raise HTTPException(404,'Asset not found')
        p=self.folder(board)/'assets'/name
        if not p.is_file():raise HTTPException(404,'Asset not found')
        return p
    def put_asset(self,board,source,suffix='.png'):
        p=Path(source)
        with p.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
        name=digest+suffix
        target=self.folder(board)/'assets'/name
        if not target.exists():shutil.copyfile(p,target)
        return name
    def append(self,board,image,preview,width,height,name,kind='image',parent=None,source=None,settings=None,stage='source',record=True):
        b=self.read(board);parent_node=next((n for n in b['nodes'] if n['id']==parent),None)
        w=560;h=w*height/width
        x=(parent_node['pose']['x']+parent_node['pose']['width']+160) if parent_node else 0
        y=parent_node['pose']['y'] if parent_node else len(b['nodes'])*80
        for _ in range(2000):
            if not any(abs(n['pose']['x']-x)<w+60 and abs(n['pose']['y']-y)<max(h,n['pose']['height'])+110 for n in b['nodes']):break
            y+=h+150
        n=dict(id=uuid.uuid4().hex,name=name[:160],kind=kind,asset=image,preview=preview,width=width,height=height,
               parentId=parent,source=source,stage=stage,created=time.time(),pose=dict(x=x,y=y,width=w,height=h),
               frame=dict(x=-60,y=-60,width=w+120,height=h+120),annotations=[],params=params(settings or {}),hidden=False,archived=False)
        self.init_node(n)
        b['nodes'].append(n);b['selectedId']=n['id']
        if kind=='image':b['nodes']=layout.arrange(b['nodes'],b['view'].get('canvasCollapsed',[]))
        self.commit(b,record=record);return next(r for r in b['nodes'] if r['id']==n['id'])
    def patch(self,id,body):
        b=self.read(id)
        if body.get('revision')!=b['revision']:raise HTTPException(409,'Board changed in another view. Your unsaved changes are retained; reload before saving.')
        if 'marks' in body:b['marks']=annotations(body['marks'])
        if 'name' in body:
            if not isinstance(body['name'],str) or not 0<len(body['name'].strip())<=160:raise ValueError('Invalid name')
            b['name']=body['name'].strip()
        if 'view' in body:
            v=body['view'];c=v['camera']
            if v['mode'] not in ('list','canvas'):raise ValueError('Invalid view')
            b['view']=dict(canvasCollapsed=[ident(x) for x in v.get('canvasCollapsed',[])][:1000],collapsed=[ident(x) for x in v.get('collapsed',[])][:1000],mode=v['mode'],camera=dict(x=finite(c['x']),y=finite(c['y']),scale=finite(c['scale'],.03,8)))
        if 'selectedId' in body:
            if body['selectedId'] is not None and not any(n['id']==body['selectedId'] for n in b['nodes']):raise ValueError('Unknown selection')
            b['selectedId']=body['selectedId']
        deltas={p['id']:(p['pose']['x']-n['pose']['x'],p['pose']['y']-n['pose']['y']) for p in body.get('nodes',[]) for n in b['nodes'] if p['id']==n['id'] and n['kind']=='image' and 'pose' in p}
        expected_layout={n['id']:n for n in layout.placements(b['nodes'],{v['id']:{k:v['pose'][k] for k in ('x','y')} for v in body.get('nodes',[]) if 'pose' in v})}
        frame_changed=[]
        seen=set()
        for patch in body.get('nodes',[]):
            if patch['id'] in seen:raise ValueError('Duplicate patch')
            seen.add(patch['id']);n=next((n for n in b['nodes'] if n['id']==patch['id']),None)
            if n is None:raise ValueError('Unknown image')
            if 'name' in patch:
                if not isinstance(patch['name'],str) or not 0<len(patch['name'])<=160:raise ValueError('Invalid image name')
                n['name']=patch['name']
            reference_change=n['kind']=='reference' and any(k in patch and patch[k]!=n.get(k) for k in ('pose','hidden','archived','params'))
            if n['kind']=='image' and patch.get('archived',n['archived'])!=n['archived']:raise ValueError('Use archive action with a saved summary')
            delta=deltas.get(n.get('parentId'));ref_follows=bool(delta and 'pose' in patch and all(patch['pose'][k]==n['pose'][k]+(delta[0] if k=='x' else delta[1] if k=='y' else 0) for k in ('x','y','width','height')))
            if ref_follows and not any(k in patch and patch[k]!=n.get(k) for k in ('params','hidden','archived')):reference_change=False
            for key in ('hidden','archived'):
                if key in patch:
                    if not isinstance(patch[key],bool):raise ValueError('Expected boolean')
                    n[key]=patch[key]
            if n['kind']=='image' and patch.get('archived',n['archived'])!=n['archived']:raise ValueError('Use archive action with a saved summary')
            if 'frame' in patch and patch['frame']!=n['frame']:frame_changed.append(n['id'])
            annotation_layout='annotations' in patch and patch['annotations']==expected_layout[n['id']]['annotations']
            changed_content=('params' in patch and patch['params']!=n['params']) or ('annotations' in patch and patch['annotations']!=n['annotations'] and not annotation_layout)
            frame_change='frame' in patch and patch['frame']!=n['frame']
            for key in ('pose','frame'):
                if key in patch:
                    p=patch[key];n[key]={k:finite(p[k],1 if k in ('width','height') else -1_000_000,1_000_000) for k in ('x','y','width','height')}
            content=changed_content
            owner=n
            if (content or reference_change or frame_change) and owner.get('busy'):raise HTTPException(409,'Image generation is in progress')
            if (content or reference_change) and owner.get('locked'):raise HTTPException(409,'Unlock the image before editing its content')
            if 'params' in patch:n['params']=params(patch['params'])
            if 'annotations' in patch:n['annotations']=annotations(patch['annotations'])
            if content or reference_change or frame_change:owner['dirty']=True
        for node in frame_changed:b['nodes']=layout.avoid(b['nodes'],node,b['view'].get('canvasCollapsed',[]))
        self.migrate(b)
        # Immutable source pixels/identity/provenance cannot be forged by a layout save.
        return self.commit(b)
    def duplicate(self,id,name):
        old=self.read(id);new=self.create(name);p=self.folder(new['id'])
        shutil.copytree(self.folder(id)/'assets',p/'assets',dirs_exist_ok=True)
        new.update(marks=copy.deepcopy(old.get('marks',[])),nodes=copy.deepcopy(old['nodes']),view=old['view'],selectedId=old['selectedId'],history=old.get('history',[]))
        return self.commit(new)
    def package(self,id):
        b=self.read(id);p=self.folder(id);target=p/('board-'+uuid.uuid4().hex+'.sflowboard');temp=p/(uuid.uuid4().hex+'.zip')
        history={t['id']:t for t in b.get('history',[])}
        for task in (p/'tasks').glob('*/task.json'):
            t=read_json(task);s=read_json(task.parent/'snapshot.json')
            t['inputs']=dict(node=s['node'],references=[r['node'] for r in s.get('references',[])],revision=s.get('revision'),inputVersion=s.get('inputVersion'),inputNotes=s.get('inputNotes',[]))
            history[t['id']]=t
        b['history']=list(history.values())
        with zipfile.ZipFile(temp,'w',compression=zipfile.ZIP_STORED) as z:
            z.writestr('board.json',json.dumps(b,ensure_ascii=False))
            for asset in (p/'assets').iterdir():
                if ASSET.fullmatch(asset.name):z.write(asset,'assets/'+asset.name)
        os.replace(temp,target);return target
    def unpack(self,path):
        with zipfile.ZipFile(path) as z:
            files=z.infolist()
            if len(files)>10000 or sum(f.file_size for f in files)>2_000_000_000:raise ValueError('Board package too large')
            names=set()
            for f in files:
                if f.filename in names:raise ValueError('Duplicate archive entry')
                names.add(f.filename)
                if f.filename!='board.json' and not re.fullmatch(r'assets/[a-f0-9]{64}(?:-preview)?\.(png|jpg|webp|psd)',f.filename):raise ValueError('Invalid archive path')
                if (f.external_attr>>16)&0o170000==0o120000:raise ValueError('Links are not allowed')
            if z.getinfo('board.json').file_size>12_000_000:raise ValueError('Board metadata too large')
            old=json.loads(z.read('board.json'))
            if old.get('schemaVersion')!=1 or len(old.get('nodes',[]))>1000:raise ValueError('Unsupported board')
            # Validate every node before publishing; local paths in a package are never executed.
            ids={ident(n['id']) for n in old['nodes']}
            if len(ids)!=len(old['nodes']):raise ValueError('Duplicate image ID')
            for n in old['nodes']:
                params(n['params']);annotations(n['annotations']);finite(n['width'],1,8192);finite(n['height'],1,8192)
                controls=n.get('guideControls',{})
                if not isinstance(controls,dict) or set(controls)-{'visible','enabled','specialVisible','specialEnabled'} or any(type(v) is not bool for v in controls.values()):raise ValueError('Invalid guide controls')
                for k in ('contextVisible','contextEnabled'):
                    if k in n and type(n[k]) is not bool:raise ValueError('Invalid reference controls')
                for a in annotations(n['annotations']):
                    if a.get('raster') and 'assets/'+a['raster'] not in names:raise ValueError('Missing instruction raster')
                for key in ('asset','preview'):
                    if not ASSET.fullmatch(n[key]) or 'assets/'+n[key] not in names:raise ValueError('Missing image asset')
                if n.get('parentId') and n['parentId'] not in ids:raise ValueError('Missing parent image')
                psd=(n.get('source') or {}).get('psdAsset')
                if psd and (not ASSET.fullmatch(psd) or 'assets/'+psd not in names):raise ValueError('Missing source PSD')
                ref=n.get('editReference')
                if ref:
                    if not isinstance(ref,dict) or any(type(ref.get(k,True)) is not bool for k in ('enabled','visible')):raise ValueError('Invalid editing reference')
                    for key in ('asset','preview','project','sourceAsset'):
                        name=ref.get(key,'')
                        if not ASSET.fullmatch(name) or 'assets/'+name not in names:raise ValueError('Missing editing reference asset')
                    finite(ref.get('width'),1,8192);finite(ref.get('height'),1,8192)
                    if not ref['project'].endswith('.psd'):raise ValueError('Invalid editing reference project')
                chain=set();parent=n
                while parent.get('parentId'):
                    if parent['id'] in chain:raise ValueError('Cyclic version relationship')
                    chain.add(parent['id']);parent=next(p for p in old['nodes'] if p['id']==parent['parentId'])
            for a in annotations(old.get('marks',[])):
                if a.get('raster') and 'assets/'+a['raster'] not in names:raise ValueError('Missing canvas instruction raster')
            b=self.create(str(old.get('name','Imported board'))[:160],remember=False);clean=copy.deepcopy(b);p=self.folder(b['id'])
            try:
                for f in files:
                    if f.filename.startswith('assets/'):
                        name=Path(f.filename).name;target=p/'assets'/name
                        with z.open(f) as source,target.open('wb') as output:shutil.copyfileobj(source,output,1024*1024)
                        with target.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
                        if '-preview' not in name and digest!=name.split('.')[0]:raise ValueError('Asset hash mismatch')
                patch=dict(revision=0,view=old['view'],nodes=[{k:n[k] for k in ('id','name','pose','frame','params','annotations','hidden','archived') if k in n} for n in old['nodes']])
                b.update(marks=annotations(old.get('marks',[])),nodes=copy.deepcopy(old['nodes']),selectedId=old.get('selectedId'),history=old.get('history',[]));write_json(p/'board.json',b)
                b=self.patch(b['id'],patch);self.preference(lastBoard=b['id']);return b
            except Exception:
                # Keep a recoverable failed import, never remove an existing board.
                clean.update(name=clean['name']+' (invalid import)',invalid=True);write_json(p/'board.json',clean);raise

    def init_node(self,n):
        original=n.get('stage')=='source' and n.get('kind')=='image' and not n.get('parentId')
        if n['kind']=='reference':n['parentId']=None
        n['params']=params(n['params'])
        n.setdefault('original',original);n.setdefault('locked',n.get('kind')=='image')
        if n['original']:n['locked']=False
        n.setdefault('deleted',False);n.setdefault('pending',False);n.setdefault('dirty',False);n.setdefault('versions',[])
        n.setdefault('versionId',hashlib.sha256((n['id']+n['asset']).encode()).hexdigest()[:32]);n.setdefault('backupLimit',None);n.setdefault('autoPrune',False)
        if not Path(n['name']).suffix.lower() in ('.psd','.psb','.png','.jpg','.jpeg','.webp'):
            n['name']+=('.psd' if (n.get('source') or {}).get('psdAsset') else '.png')
    def migrate(self,b):
        b.setdefault('marks',[]);b['view'].setdefault('collapsed',[]);b['view'].setdefault('canvasCollapsed',[])
        for n in b['nodes']:self.init_node(n)
        for n in b['nodes']:
            parent=next((r for r in b['nodes'] if r['id']==n.get('parentId')),None)
            if parent and n['kind']=='image':n.setdefault('input',self.pixel_snapshot(parent))
            n.setdefault('baseline',self.configuration(b,n))
        self.statuses(b)
    def pixel_snapshot(self,n):
        return {k:copy.deepcopy(n.get(k)) for k in ('id','versionId','asset','preview','width','height','source','stage')}
    def configuration(self,b,n):
        return dict(contextSignature=context.signature(b,n),params=copy.deepcopy(n['params']),annotations=copy.deepcopy(n['annotations']),frame=copy.deepcopy(n['frame']),
                    references=[copy.deepcopy(r['node']) for r in context.collected(b,n)[1]])
    def effective(self,b,n):
        parent=next((r for r in b['nodes'] if r['id']==n.get('parentId')),None);skipped=[]
        while parent and parent.get('archived'):
            skipped.insert(0,dict(id=parent['id'],summary=parent.get('archiveSummary','')))
            parent=next((r for r in b['nodes'] if r['id']==parent.get('parentId')),None)
        return parent,skipped
    def statuses(self,b):
        for n in b['nodes']:
            parent,skipped=self.effective(b,n);current=n.get('input') or {}
            n['inputChanged']=bool(parent and (parent['versionId']!=current.get('versionId') or parent['id']!=current.get('id') or skipped!=n.get('inputNotes',[])))
    def branch(self,id,node,sibling=False,stage=None):
        b=self.read(id);before=copy.deepcopy(b);n=next(r for r in b['nodes'] if r['id']==node)
        if n.get('deleted'):raise ValueError('Image was deleted')
        if len(b['nodes'])>=1000:raise ValueError('Board image limit reached; create another board')
        if n['kind']!='image' or n.get('pending'):raise ValueError('Choose a completed image')
        if sibling and n['original']:raise ValueError('Original inputs only support child creation')
        parent,notes=self.effective(b,n) if sibling else (n,[])
        if not parent:raise ValueError('Input image unavailable')
        if parent.get('pending'):raise ValueError('Generate the input image first')
        settings=copy.deepcopy(n['params'])
        if stage is not None:
            if stage not in ('whole','detail'):raise ValueError('stage: whole | detail')
            if stage=='detail' and (parent.get('original') or parent.get('stage') not in ('whole','detail')):raise ValueError('Choose a completed generated image for high-resolution output')
            settings['generationStage']=stage
        if not n['original']:settings['prompt']=''
        r=self.append(id,parent['asset'],parent['preview'],parent['width'],parent['height'],Path(n['name']).stem+' · '+str(len(b['nodes'])+1)+'.png',parent=parent['id'],stage='draft',settings=settings,record=False)
        b=self.read(id);r=next(v for v in b['nodes'] if v['id']==r['id'])
        r.update(original=False,locked=False,pending=True,dirty=True,input=self.pixel_snapshot(parent),inputNotes=notes)
        # A sibling keeps the logical parent, even when that parent is archived.
        if sibling:r['parentId']=n['parentId'];r['input']=copy.deepcopy(n.get('input') or self.pixel_snapshot(parent));r['inputNotes']=copy.deepcopy(n.get('inputNotes',[]))
        key='canvasCollapsed' if b['view']['mode']=='canvas' else 'collapsed';chain=set();current=r
        while current:
            chain.add(current['id']);current=next((v for v in b['nodes'] if v['id']==current.get('parentId')),None)
        b['view'][key]=[x for x in b['view'].get(key,[]) if x not in chain];b['nodes']=layout.arrange(b['nodes'],b['view'].get('canvasCollapsed',[]))
        self.commit(b,before=before);return next(v for v in b['nodes'] if v['id']==r['id'])
    def capacity(self,n):
        return n['backupLimit'] if n.get('backupLimit') is not None else self.preference()['backupLimit']
    def check_capacity(self,n):
        if not n['pending'] and len(n['versions'])>=self.capacity(n) and not n.get('autoPrune'):
            raise HTTPException(409,'Backup capacity reached. Delete a backup, enable automatic cleanup, or expand this image capacity.')
    def control(self,id,node,body):
        b=self.read(id)
        if body.get('revision')!=b['revision']:raise HTTPException(409,'Board changed; reload before this operation')
        n=next(r for r in b['nodes'] if r['id']==node);action=body['action']
        if action=='delete':
            ids={node}
            for _ in range(len(b['nodes'])):
                added={r['id'] for r in b['nodes'] if r.get('parentId') in ids};old=len(ids);ids.update(added)
                if len(ids)==old:break
            if any(r.get('busy') for r in b['nodes'] if r['id'] in ids):raise HTTPException(409,'Finish tasks in this branch before deleting')
            token=uuid.uuid4().hex
            for r in b['nodes']:
                if r['id'] in ids and not r.get('deleted'):r.update(deleted=True,deletedBy=token)
            b['selectedId']=n.get('parentId') if n.get('parentId') not in ids else None
            if b['selectedId'] and next(r for r in b['nodes'] if r['id']==b['selectedId']).get('deleted'):b['selectedId']=None
            if n['kind']=='image':b['nodes']=layout.arrange(b['nodes'],b['view'].get('canvasCollapsed',[]))
            else:b['selectedId']=next((v['id'] for v in b['nodes'] if v['kind']=='image' and not v.get('deleted') and v['id']==self.read(id).get('selectedId')),next((v['id'] for v in b['nodes'] if v['kind']=='image' and not v.get('deleted')),None))
        elif action=='restoreDeleted':
            token=n.get('deletedBy')
            for r in b['nodes']:
                if token and r.get('deletedBy')==token:r['deleted']=False;r.pop('deletedBy',None)
            b['selectedId']=node;b['nodes']=layout.arrange(b['nodes'],b['view'].get('canvasCollapsed',[]))
        elif action=='applyParent':
            if not n['pending'] or n.get('busy'):raise ValueError('Only an idle draft can apply its parent')
            parent=n.get('input')
            if not parent or not parent.get('asset'):raise ValueError('Draft has no pinned parent input')
            for key in ('asset','preview','width','height'):n[key]=copy.deepcopy(parent[key])
            n['draftBaseApplied']=True;n['dirty']=True
        elif action=='lock':
            if n['original']:raise ValueError('Original input settings stay unlocked')
            if n.get('busy'):raise ValueError('Wait for generation before locking')
            n['locked']=True
        elif action=='convertToInput':
            if n['kind']!='reference' or n.get('deleted') or n.get('busy'):raise ValueError('Choose a live reference resource')
            n.update(kind='image',original=True,locked=False,parentId=None,pending=False,stage='source',frame=dict(x=-60,y=-60,width=n['pose']['width']+120,height=n['pose']['height']+120))
            n['source']={**(n.get('source') or {}), 'convertedFromReference':True}
            b['selectedId']=node;b['nodes']=layout.arrange(b['nodes'],b['view'].get('canvasCollapsed',[]));n=next(v for v in b['nodes'] if v['id']==node);n['baseline']=self.configuration(b,n)
        elif action=='unlock':
            n['locked']=False
        elif action=='cancel':
            n.pop('checkout',None)
            c=n['baseline'];n.update(params=copy.deepcopy(c['params']),annotations=copy.deepcopy(c['annotations']),frame=copy.deepcopy(c['frame']),dirty=n['pending'],locked=not n['pending'] and not n['original'])
        elif action=='archive':
            if n['original'] or n['pending']:raise ValueError('Only completed generated images can be archived')
            summary=body.get('summary','').strip()
            if not summary:raise ValueError('Generate an archive summary first')
            n.update(archived=True,archiveSummary=summary[:16000])
        elif action=='restore':n['archived']=False
        elif action=='followBackupDefault':n['backupLimit']=None
        elif action=='expand':n['backupLimit']=self.capacity(n)+3
        elif action=='autoPrune':n['autoPrune']=bool(body.get('enabled'))
        elif action=='deleteBackup':
            if n.get('checkout')==body['version']:raise ValueError('Cancel the backup edit before deleting that backup')
            n['versions']=[v for v in n['versions'] if v['versionId']!=body['version']]
        elif action=='checkout':
            if n['original']:raise ValueError('Original input is read-only')
            v=next(v for v in n['versions'] if v['versionId']==body['version'])
            n.update(params=copy.deepcopy(v['configuration']['params']),annotations=copy.deepcopy(v['configuration']['annotations']),frame=copy.deepcopy(v['configuration']['frame']),dirty=True,locked=False,checkout=v['versionId'])
        elif action=='deleteDraft':
            if not n['pending']:raise ValueError('Only a pending draft can be deleted')
            b['nodes']=[r for r in b['nodes'] if r['id']!=node and r.get('parentId')!=node];b['selectedId']=n.get('parentId')
        else:raise ValueError('Unknown node action')
        if action=='deleteBackup' and len(n['versions'])<=self.preference()['backupLimit']:n['backupLimit']=None
        self.statuses(b);return self.commit(b)
    def publish(self,id,node,image,preview,width,height,stage,source,snapshot):
        b=self.read(id);n=next(r for r in b['nodes'] if r['id']==node)
        if n['original']:raise ValueError('Create a child result; original input pixels cannot be replaced')
        self.check_capacity(n)
        if not n['pending']:
            old=self.pixel_snapshot(n);old.update(configuration=copy.deepcopy(n['baseline']),created=time.time(),input=copy.deepcopy(n.get('input')),inputNotes=copy.deepcopy(n.get('inputNotes',[])))
            n['versions'].append(old)
        n.update(asset=image,preview=preview,width=width,height=height,stage=stage,source=source,versionId=uuid.uuid4().hex,
                 input=copy.deepcopy(snapshot['inputVersion']),inputNotes=copy.deepcopy(snapshot.get('inputNotes',[])),pending=False,locked=True,dirty=False)
        if snapshot.get('contextSignature') is not None:n['dirty']=context.signature(b,n)!=snapshot['contextSignature']
        n['baseline']=self.configuration(b,n);n.pop('checkout',None)
        template=snapshot.get('inputTemplate')
        if template:
            root=next((v for v in b['nodes'] if v['id']==template['id'] and v.get('original')),None)
            if root and root['params']['prompt']==template['prompt']:
                root['params']['prompt']='';root['locked']=False
                root['dirty']=False;root['baseline']=self.configuration(b,root)
        limit=self.capacity(n)
        if n.get('autoPrune') and len(n['versions'])>limit:n['versions']=n['versions'][-limit:] if limit else []
        if n.get('backupLimit') is not None and len(n['versions'])<=self.preference()['backupLimit']:n['backupLimit']=None
        self.statuses(b);b['selectedId']=node;self.commit(b,barrier=True);return n

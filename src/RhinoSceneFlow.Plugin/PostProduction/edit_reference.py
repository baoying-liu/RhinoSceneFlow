"""Single replaceable PhotoCraft reference slot. Never publishes a result/version."""
import asyncio, time, uuid, copy, math
from pathlib import Path
from fastapi import HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from project import read_json, write_json
from board_store import ident
import guide_layers as guides
import canvas_context as context

HERE = Path(__file__).resolve().parent
MAX_PROJECT = 256 * 1024 * 1024

def register(app, boards):
    store = boards.store
    applying = set()

    @app.get('/editor/photocraft/{name:path}')
    async def editor_asset(name: str):
        root = (HERE/'vendor'/'photocraft').resolve()
        # v0.21's app glue imports ./snippets while the release zip stores them at root.
        if name.startswith('app/snippets/'):name=name[4:]
        path = (root/(name or 'index.html')).resolve()
        if not path.is_relative_to(root) or not path.is_file():raise HTTPException(404)
        if path.name == 'index.html':
            # The upstream distribution stays byte-identical; this host supplies its adapter.
            html = path.read_text(encoding='utf-8').replace('<head>', '<head><script src="/photocraft-bridge.js"></script>', 1)
            return HTMLResponse(html)
        return FileResponse(path, media_type='application/wasm' if path.suffix=='.wasm' else None)

    @app.get('/photocraft-bridge.js')
    async def bridge():return FileResponse(HERE/'photocraft-bridge.js',media_type='text/javascript')

    def target(id, node):
        b = store.read(id);n = boards.node(b, node)
        if n.get('deleted') or n.get('archived') or n.get('busy'):raise HTTPException(409,'Image unavailable or busy')
        if n.get('checkout'):raise HTTPException(409,'Exit backup checkout before editing the current reference')
        if n.get('pending') and not n.get('draftBaseApplied'):raise ValueError('Apply the parent image to the draft first')
        return b,n

    def slot_key(n):return (n.get('editReference') or {}).get('project')

    def session(id, sid):
        folder = store.folder(id)/'editor'/ident(sid)
        if not (folder/'session.json').is_file():raise HTTPException(404,'Editor session not found')
        s = read_json(folder/'session.json')
        if s.get('applied') or time.time()-s['created']>86400:raise HTTPException(409,'Editor session expired; reopen the editor')
        return folder,s

    @app.post('/api/boards/{id}/nodes/{node}/edit-reference/session')
    async def start(id: str, node: str, request: Request):
        body=await request.json();b,n=target(id,node)
        if body.get('revision')!=b['revision']:raise HTTPException(409,'Board changed; reload before editing')
        folder=store.folder(id)/'editor'/uuid.uuid4().hex;folder.mkdir(parents=True)
        if n.get('locked'):raise HTTPException(409,'Unlock the image before editing in PhotoCraft')
        s=dict(node=node,sourceAsset=n['asset'],versionId=n['versionId'],previous=slot_key(n),contextKey=guides.content_key(b,n),created=time.time())
        ref=n.get('editReference') or {}
        scale=n['width']/n['pose']['width'];f=n['frame'] if n['kind']=='image' else dict(x=0,y=0,width=n['pose']['width'],height=n['pose']['height']);ox=max(0,math.ceil(-f['x']*scale));oy=max(0,math.ceil(-f['y']*scale))
        layout=dict(width=max(n['width']+ox,math.ceil((f['x']+f['width'])*scale)+ox),height=max(n['height']+oy,math.ceil((f['y']+f['height'])*scale)+oy),offset=[ox,oy],scale=scale,imageSize=[n['width'],n['height']])
        if max(layout['width'],layout['height'])>8192:raise ValueError('Consideration-frame editor limit: 8192 px per side; reduce the frame')
        values=guides.items(b,n)
        for v in values:
            if v['kind']=='reference':
                r=v.pop('resource');v['originalSize']=[r['width'],r['height']];edited=r.get('editReference') or {};asset=edited['asset'] if edited.get('sourceAsset')==r['asset'] else r['asset'];v['path']=str(store.asset(id,asset))
            elif v['annotation'].get('raster'):v['path']=str(store.asset(id,v['annotation']['raster']))
        spec=dict(image=str(store.asset(id,n['asset'])),layout=layout,items=values,specialVisible=guides.gate(n,'specialVisible'))
        if ref.get('sourceAsset')==n['asset'] and ref.get('project'):spec.update(previous=str(store.asset(id,ref['project'])),previousLayout=ref.get('layout'))
        write_json(folder/'editor.json',spec)
        job=boards.api['new_job'](id,'reference-editor');job.update(status='running',stage='Preparing editor')
        try:await boards.raster(job,'editor-seed',folder)
        except BaseException:
            job.update(status='failed',stage='Editor preparation failed');raise
        else:job.update(status='completed',stage='Editor ready')
        write_json(folder/'session.json',s)
        return dict(session=folder.name,name=Path(n['name']).stem+'-reference.psd',path=str(folder/'reference.psd'))

    @app.get('/api/boards/{id}/edit-reference/{sid}/input')
    async def input_file(id: str, sid: str):
        folder,s=session(id,sid)
        return FileResponse(folder/'reference.psd',media_type='image/vnd.adobe.photoshop')

    @app.delete('/api/boards/{id}/edit-reference/{sid}')
    async def cancel_session(id: str, sid: str):
        if sid in applying:raise HTTPException(409,'Wait for Apply to finish')
        folder=store.folder(id)/'editor'/ident(sid)
        if folder.is_dir():
            for path in folder.iterdir():
                if path.suffix in ('.png','.psd','.json'):path.unlink(missing_ok=True)
            try:folder.rmdir()
            except OSError:pass # Worker logs, if present, are diagnostic data, never backups.
        return dict(cancelled=True)

    @app.post('/api/boards/{id}/edit-reference/{sid}/apply')
    async def apply(id: str, sid: str, request: Request):
        ident(sid)
        if sid in applying:raise HTTPException(409,'Reference save is already running')
        applying.add(sid)
        try:return await apply_project(id,sid,request)
        finally:applying.discard(sid)

    @app.post('/api/boards/{id}/edit-reference/{sid}/apply-file')
    async def apply_file(id: str,sid: str,request: Request):
        # JSON transport for the original Rhino MCP Platform. The source is read-only.
        body=await request.json();path=Path(body.get('path',''))
        if not path.is_absolute() or path.suffix.lower()!='.psd' or not path.is_file():raise ValueError('Choose an absolute PSD project path')
        before=path.stat()
        if before.st_size>MAX_PROJECT:raise HTTPException(413,'Editor project exceeds 256 MB')
        class ProjectFile:
            async def stream(self):
                with path.open('rb') as stream:
                    while chunk:=await asyncio.to_thread(stream.read,1024*1024):yield chunk
                after=path.stat()
                if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):raise ValueError('The PSD changed while reading; save and retry')
        return await apply(id,sid,ProjectFile())

    async def apply_project(id, sid, request):
        folder,s=session(id,sid);b,n=target(id,s['node'])
        def fresh(n):
            if (n['asset'],n['versionId'],slot_key(n))!=(s['sourceAsset'],s['versionId'],s['previous']):
                raise HTTPException(409,'The source or reference changed. Reopen the editor before applying.')
            if n.get('locked') or guides.content_key(b,n)!=s.get('contextKey',guides.content_key(b,n)):raise HTTPException(409,'Instructions, frame or lock changed. Reopen PhotoCraft before applying.')
        fresh(n)
        total=0
        # Fixed destination, never use a caller-provided path or filename.
        with (folder/'upload.psd').open('wb') as out:
            async for data in request.stream():
                total+=len(data)
                if total>MAX_PROJECT:raise HTTPException(413,'Editor project exceeds 256 MB')
                out.write(data)
        if not total:raise ValueError('Empty editor project')
        job=boards.api['new_job'](id,'reference-editor');job.update(status='running',stage='Reading edited reference')
        try:
            await boards.raster(job,'editor-read',folder)
            b,n=target(id,s['node']);fresh(n) # A slow worker must not overwrite a newer slot.
            info=read_json(folder/'image.json')
            previous=n.get('editReference') or {};manifest=read_json(folder/'layers-manifest.json');returned=read_json(folder/'layers-return.json')
            before={a['id']:a for a in manifest['items']};changed=[]
            for item in returned['instructions']:
                home=before[item['id']]['home'];owner=boards.node(b,home) if home else None
                if item['changed'] and owner and (owner.get('locked') or owner.get('busy')):raise HTTPException(409,'An instruction belongs to another locked/busy image. Unlock its owner before applying.')
            project=store.put_asset(id,folder/'upload.psd','.psd')
            for item in returned['instructions']:
                original=before[item['id']]
                if item.get('file'):item['asset']=store.put_asset(id,folder/item['file'])
                if item['kind']=='reference':
                    resource=boards.node(b,item['id'])
                    if item.get('deleted'):resource['deleted']=True;changed.append(item['id']);continue
                    if item['visible']!=original['visible']:resource['contextVisible']=item['visible']
                    if item['changed']:
                        q=item['pose'];resource['pose']=dict(q,x=q['x']+n['pose']['x'],y=q['y']+n['pose']['y'])
                        asset=store.put_asset(id,folder/('reference-'+item['id']+'.png'));old=resource.get('editReference') or {}
                        from PIL import Image
                        with Image.open(folder/('reference-'+item['id']+'.png')) as im:w,h=im.size
                        resource['editReference']=dict(project=store.put_asset(id,folder/('reference-'+item['id']+'.psd'),'.psd'),asset=asset,preview=asset,width=w,height=h,sourceAsset=resource['asset'],enabled=old.get('enabled',True),visible=old.get('visible',True),updated=time.time());changed.append(item['id'])
                else:
                    home=original['home'];arr=boards.node(b,home)['annotations'] if home else b['marks'];a=next(x for x in arr if x['id']==item['id'])
                    if item.get('deleted'):arr.remove(a);changed.append(item['id']);continue
                    if item['visible']!=original['visible']:a['visible']=item['visible']
                    if item['changed']:
                        q=item['pose'];homepose=boards.node(b,home)['pose'] if home else dict(x=0,y=0)
                        a.update(raster=store.put_asset(id,folder/item['file']),rasterPose=dict(q,x=q['x']+n['pose']['x']-homepose['x'],y=q['y']+n['pose']['y']-homepose['y']),points=[],text='');changed.append(item['id'])
            if returned.get('specialVisible',True)!=read_json(folder/'editor.json').get('specialVisible',True):n.setdefault('guideControls',{})['specialVisible']=returned['specialVisible']
            declaration=copy.deepcopy(returned)
            for item in declaration['instructions']:item.pop('file',None)
            n['editReference']=dict(project=project,
                asset=store.put_asset(id,folder/'image.png'),preview=store.put_asset(id,folder/'preview.png'),
                width=info['width'],height=info['height'],sourceAsset=s['sourceAsset'],enabled=previous.get('enabled',True),
                visible=previous.get('visible',True),layout=info.get('layout'),declaration=declaration,updated=time.time())
            # Appearance stays outside undo; actual annotation/resource changes are
            # board edits and remain undoable (Store strips editReference slots).
            store.commit(b,record=bool(changed))
            s['applied']=True;write_json(folder/'session.json',s)
            job.update(status='completed',stage='Reference applied')
            # Session scratch files are not additional reference backups. Published hashes
            # stay immutable for frozen generation jobs and portable board packages.
            for path in folder.iterdir():
                if path.suffix in ('.png','.psd','.json') and path.name!='session.json':path.unlink(missing_ok=True)
            return store.read(id)
        except BaseException:
            job.update(status='failed',stage='Reference not applied');raise

    @app.post('/api/boards/{id}/nodes/{node}/edit-reference/control')
    async def control(id: str,node: str,request: Request):
        body=await request.json()
        if body.get('action')=='visibility':
            b=store.read(id);n=boards.node(b,node)
            if n.get('deleted'):raise HTTPException(409,'Image was deleted')
        else:
            b,n=target(id,node)
            if n.get('locked'):raise HTTPException(409,'Unlock the image before changing its editing reference')
        if body.get('revision')!=b['revision']:raise HTTPException(409,'Board changed; reload first')
        if body.get('action')=='remove':n.pop('editReference',None)
        elif body.get('action')=='toggle' and n.get('editReference'):n['editReference']['enabled']=not n['editReference'].get('enabled',True)
        elif body.get('action')=='visibility' and n.get('editReference'):
            if type(body.get('visible')) is not bool:raise ValueError('visible must be boolean')
            n['editReference']['visible']=body['visible']
        else:raise ValueError('action: remove | toggle | visibility')
        return store.commit(b,record=False)

    @app.post('/api/boards/{id}/nodes/{node}/guide-control')
    async def guide_control(id:str,node:str,request:Request):
        body=await request.json();b=store.read(id);n=boards.node(b,node)
        if n.get('deleted'):raise HTTPException(409,'Image deleted')
        if b['revision']!=body.get('revision'):raise HTTPException(409,'Board changed; reload first')
        field=body.get('field');scope=body.get('scope');value=body.get('value')
        if field not in ('visible','enabled') or type(value) is not bool:raise ValueError('field: visible | enabled; value: boolean')
        if field=='enabled' and (n.get('locked') or n.get('busy') or n.get('archived')):raise HTTPException(409,'Unlock the idle image before changing AI participation')
        if scope in ('all','special'):
            key=field if scope=='all' else 'special'+field.title();n.setdefault('guideControls',{})[key]=value
        elif scope=='appearance':
            if not n.get('editReference'):raise ValueError('No appearance reference')
            n['editReference'][field]=value
        else:
            item=next((a for a in guides.items(b,n) if a['id']==body.get('layer')),None)
            if not item:raise ValueError('Instruction is no longer inside this consideration frame')
            if item['kind']=='reference':boards.node(b,item['id'])['context'+field.title()]=value
            else:
                home=item['home'];owner=boards.node(b,home) if home else None
                if field=='enabled' and owner and (owner.get('locked') or owner.get('busy')):raise HTTPException(409,'Unlock the instruction owner before changing participation')
                a=next(a for a in (owner['annotations'] if owner else b['marks']) if a['id']==item['id']);a[field]=value
        return store.commit(b,record=False)

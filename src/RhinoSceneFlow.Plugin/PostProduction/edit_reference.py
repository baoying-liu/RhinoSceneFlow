"""Single replaceable PhotoCraft reference slot. Never publishes a result/version."""
import asyncio, time, uuid
from pathlib import Path
from fastapi import HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from project import read_json, write_json
from board_store import ident

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
        s=dict(node=node,sourceAsset=n['asset'],versionId=n['versionId'],previous=slot_key(n),created=time.time())
        ref=n.get('editReference') or {}
        if ref.get('sourceAsset')==n['asset'] and ref.get('project'):
            import shutil
            shutil.copyfile(store.asset(id,ref['project']),folder/'reference.psd')
        else:
            write_json(folder/'editor.json',dict(image=str(store.asset(id,n['asset']))))
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
            for name in ('upload.psd','reference.psd','image.png','preview.png','image.json','editor.json','session.json'):
                (folder/name).unlink(missing_ok=True)
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
            n['editReference']=dict(project=store.put_asset(id,folder/'upload.psd','.psd'),
                asset=store.put_asset(id,folder/'image.png'),preview=store.put_asset(id,folder/'preview.png'),
                width=info['width'],height=info['height'],sourceAsset=s['sourceAsset'],enabled=True,
                visible=(n.get('editReference') or {}).get('visible',True),updated=time.time())
            store.commit(b,record=False)
            s['applied']=True;write_json(folder/'session.json',s)
            job.update(status='completed',stage='Reference applied')
            # Session scratch files are not additional reference backups. Published hashes
            # stay immutable for frozen generation jobs and portable board packages.
            for name in ('upload.psd','reference.psd','image.png','preview.png','image.json','editor.json'):
                (folder/name).unlink(missing_ok=True)
            return store.read(id)
        except BaseException:
            job.update(status='failed',stage='Reference not applied');raise

    @app.post('/api/boards/{id}/nodes/{node}/edit-reference/control')
    async def control(id: str,node: str,request: Request):
        body=await request.json()
        if body.get('action')=='visibility':
            b=store.read(id);n=boards.node(b,node)
            if n.get('deleted'):raise HTTPException(409,'Image was deleted')
        else:b,n=target(id,node)
        if body.get('revision')!=b['revision']:raise HTTPException(409,'Board changed; reload first')
        if body.get('action')=='remove':n.pop('editReference',None)
        elif body.get('action')=='toggle' and n.get('editReference'):n['editReference']['enabled']=not n['editReference'].get('enabled',True)
        elif body.get('action')=='visibility' and n.get('editReference'):
            if type(body.get('visible')) is not bool:raise ValueError('visible must be boolean')
            n['editReference']['visible']=body['visible']
        else:raise ValueError('action: remove | toggle | visibility')
        return store.commit(b,record=False)

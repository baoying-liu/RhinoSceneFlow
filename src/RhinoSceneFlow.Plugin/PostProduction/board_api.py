import canvas_context as context
"""Board transport and explicit two-stage jobs. Shares the existing owned image runner."""
import asyncio, copy, hashlib, json, shutil, sys, time, uuid
import os
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from board_store import Store, ident, params
from project import read_json, write_json

HERE=Path(__file__).resolve().parent

class BoardApi:
    def __init__(self,root,api,generation):
        self.store=Store(root);self.api=api;self.generation=generation;self.active={}
    async def raster(self,job,operation,folder):
        async with self.api['gate']:
            self.check(job)
            code,_,error=await self.api['run_process'](job,[sys.executable,'-I','-X','utf8',str(HERE/'board_render.py'),operation,str(folder)],timeout=600,directory=folder)
            if code:raise ValueError(error.strip().splitlines()[-1][-400:] if error.strip() else 'Image worker failed')
    def check(self,job):
        if job['status']=='cancelled':raise asyncio.CancelledError()
    def cancel(self,id):
        if id in self.active:self.active[id].cancel()
    def track(self,job,runner,folder,task):
        self.active[job['id']]=runner
        def done(future):
            self.active.pop(job['id'],None)
            if future.cancelled() and task['status'] in ('queued','running'):
                task.update(status='cancelled',phase='cancelled');job.update(status='cancelled',stage='cancelled');write_json(folder/'task.json',task)
        runner.add_done_callback(done)
    def task_folder(self,id):
        p=self.store.folder(id)/'tasks'/uuid.uuid4().hex;p.mkdir();return p
    def node(self,board,node):
        n=next((n for n in board['nodes'] if n['id']==node),None)
        if n is None:raise HTTPException(404,'Image not found')
        return n
    def tasks(self,id):
        result=[{**t,'imported':True, 'status':'interrupted' if t['status'] in ('running','queued') else t['status']} for t in self.store.read(id).get('history',[])]
        for p in (self.store.folder(id)/'tasks').glob('*/task.json'):
            t=read_json(p)
            if t['status'] in ('queued','running') and (t['job'] not in self.active or self.active[t['job']].done()):t.update(status='interrupted',phase='interrupted')
            if t['status'] in ('review','failed') and t.get('project') and t.get('run'):
                state=self.generation.state(t['project'],t['run'])
                if state['status']=='completed' and state.get('output'):
                    snapshot=read_json(p.parent/'snapshot.json');n=snapshot['node'];o=state['output'];src=self.generation.folder(t['project'],t['run'])
                    existing=next((r for r in self.store.read(id)['nodes'] if (r.get('source') or {}).get('task')==t['id']),None)
                    if existing:node=existing
                    elif 'inputVersion' in snapshot:node=self.store.publish(id,t['node'],self.store.put_asset(id,src/o['image']),self.store.put_asset(id,src/o['preview']),o['width'],o['height'],'detail',dict(task=t['id'],projectId=t['project'],runId=t['run']),snapshot)
                    else:node=self.store.append(id,self.store.put_asset(id,src/o['image']),self.store.put_asset(id,src/o['preview']),o['width'],o['height'],Path(n['name']).stem+' · HD.png',parent=n['id'],stage='detail',settings=n['params'],source=dict(task=t['id'],projectId=t['project'],runId=t['run']))
                    t.update(status='completed',phase='completed',result=node['id']);write_json(p,t)
            result.append(t)
        b=self.store.read(id);changed=False
        for n in b['nodes']:
            if n.get('busy') and not any(t['id']==n['busy'] and t['status'] in ('queued','running','review') for t in result):n.pop('busy',None);changed=True
        if changed:self.store.commit(b)
        return sorted(result,key=lambda t:t['created'],reverse=True)
    async def ingest(self,id,path,name,kind='image',owner=None):
        b=self.store.read(id)
        if len(b['nodes'])>=1000:raise ValueError('Board image limit reached')
        if kind not in ('image','reference'):raise ValueError('Invalid image type')
        if Path(name).suffix.lower() in ('.psd','.psb'):
            result=await self.api['create_project'](path,Path(name).stem)
            while self.api['jobs'][result['job']]['status'] in ('queued','running'):await asyncio.sleep(.1)
            if self.api['jobs'][result['job']]['status']!='completed':raise ValueError(self.api['jobs'][result['job']]['stage'])
            return self.add_project(id,result['project'])
        folder=self.task_folder(id);shutil.copyfile(path,folder/'upload');job=self.api['new_job'](id,'board-import')
        try:
            job.update(status='running',stage='Reading image');await self.raster(job,'ingest',folder);info=read_json(folder/'image.json')
            image=self.store.put_asset(id,folder/'image.png');preview=self.store.put_asset(id,folder/'preview.png')
            node=self.store.append(id,image,preview,info['width'],info['height'],Path(name).name,kind,parent=None)
            if kind=='reference':
                b=self.store.read(id);n=self.node(b,node['id']);n['pose'].update(width=220,height=220*info['height']/info['width']);self.store.commit(b);node=n
            job.update(status='completed',stage='Imported');return node
        except BaseException:
            job.update(status='failed',stage='Import failed');raise
    def add_project(self,id,project,run_id=None):
        existing=next((n for n in self.store.read(id)['nodes'] if not n.get('deleted') and (n.get('source') or {}).get('projectId')==project and (n.get('source') or {}).get('runId')==run_id),None)
        if existing:return existing
        state=self.api['read_project'](project)
        if state['status']!='ready':raise ValueError('Wait for PSD import to finish')
        folder=self.api['project_dir'](project);doc=state['document'];name=state['name']+'.psd';stage='source';source=dict(projectId=project)
        if run_id:
            r=self.generation.state(project,run_id)
            if not r.get('output'):raise ValueError('No completed image in this version')
            src=self.generation.folder(project,run_id);image=src/r['output']['image'];preview=src/r['output']['preview'];w,h=r['output']['width'],r['output']['height']
            source['runId']=run_id;source['partial']=r['status']!='completed';stage='detail';name+=' · '+run_id[:6]+(' · partial' if source['partial'] else '')
        else:
            image=folder/'composite.png';preview=folder/'preview.png';w,h=doc['width'],doc['height']
            source.update(psdAsset=self.store.put_asset(id,folder/'source.psd','.psd'),layers=doc['layers'])
        return self.store.append(id,self.store.put_asset(id,image),self.store.put_asset(id,preview),w,h,name,source=source,stage=stage,
            settings=dict(prompt=state['settings']['prompt'],roles=state['settings']['roles']))
    def snapshot(self,id,node):
        b=self.store.read(id);n=copy.deepcopy(self.node(b,node));folder=self.store.folder(id);p=n['pose'];f=n['frame'];references=[]
        marks,references=context.collected(b,n);n['annotations']=marks
        for r in references:r['path']=str(self.store.asset(id,r['node']['asset']))
        if len(references)>4:raise ValueError('Use up to four reference images in one generation frame')
        result=dict(board=id,revision=b['revision'],contextSignature=context.signature(b,self.node(b,node)),node=n,image=str(self.store.asset(id,n['asset'])),references=references)
        source=n.get('source') or {}
        if n['stage']=='source' and source.get('psdAsset'):
            result.update(psd=str(self.store.asset(id,source['psdAsset'])),layers=source['layers'])
        if n.get('parentId'):
            parent=next((r for r in b['nodes'] if r['id']==n['parentId']),None)
            if parent:result['parent']=str(self.store.asset(id,parent['asset']))
        return result
    def generation_snapshot(self,id,node):
        """One resolver for preflight and execution; displayed history stays pinned."""
        b=self.store.read(id);target=self.node(b,node)
        if target.get('original') or target.get('deleted') or target.get('archived'):raise ValueError('Choose an active generated-image draft')
        snapshot=self.snapshot(id,node);n=snapshot['node'];parent,notes=self.store.effective(b,target)
        if not parent or parent.get('pending'):raise ValueError('A completed input image is required')
        snapshot['inputVersion']=self.store.pixel_snapshot(parent);snapshot['inputNotes']=notes
        snapshot['inputName']=parent['name']
        if parent.get('original'):snapshot['inputTemplate']=dict(id=parent['id'],prompt=parent['params']['prompt'])
        snapshot['image']=str(self.store.asset(id,parent['asset']));snapshot['parent']=snapshot['image']
        snapshot.pop('psd',None);snapshot.pop('layers',None)
        if parent.get('original') and (parent.get('source') or {}).get('psdAsset'):
            snapshot.update(psd=str(self.store.asset(id,parent['source']['psdAsset'])),layers=parent['source']['layers'])
        n.update(asset=parent['asset'],preview=parent['preview'],width=parent['width'],height=parent['height'])
        if notes:n['params']['prompt']+='\nArchived modification intent:\n'+'\n'.join(x['summary'] for x in notes)
        return snapshot
    def prepared_input(self,s,folder):
        version=copy.deepcopy(s['inputVersion'])
        if read_json(folder/'prepared.json').get('sourceAdjusted'):
            version.update(originalAsset=version.get('originalAsset',version['asset']),asset=self.store.put_asset(s['board'],folder/'base.png'),preview=self.store.put_asset(s['board'],folder/'base-preview.png'),prepared=True)
        return version
    async def preflight(self,id,node,body):
        s=self.generation_snapshot(id,node)
        if body.get('revision')!=s['revision']:raise HTTPException(409,'Board changed; save or reload before checking input')
        stage=body.get('stage','whole')
        self.validate_stage(s,stage)
        folder=self.task_folder(id);write_json(folder/'snapshot.json',s);job=self.api['new_job'](id,'preflight')
        try:
            job.update(status='running',stage='Preparing input preview')
            await self.raster(job,'prepare' if stage=='whole' else 'detail',folder)
            images={k:self.store.put_asset(id,folder/v) for k,v in (dict(input='input.png',context='markup.png',mask='mask.png').items() if stage=='whole' else [])}
            prepared=read_json(folder/'prepared.json') if stage=='whole' else {}
            if prepared.get('guides'):images['guides']=self.store.put_asset(id,folder/'psd-guides.png')
            job.update(status='completed',stage='Input preview ready')
            actual_input=self.prepared_input(s,folder) if stage=='whole' else s['inputVersion']
            ratio=s['node']['params']['outputSize']/max(actual_input['width'],actual_input['height']) if stage=='detail' else 1
            output=dict(width=max(1,round(actual_input['width']*ratio)),height=max(1,round(actual_input['height']*ratio)))
            return dict(guides=prepared.get('guides',[]),output=output,node=node,revision=s['revision'],stage=stage,input={**actual_input,'name':s['inputName']},scope=prepared.get('scope'),sourceAdjusted=prepared.get('sourceAdjusted',False),notes=s['inputNotes'],images=images,
                annotations=s['node']['annotations'] if stage=='whole' else [],references=[dict(id=r['node']['id'],name=r['node']['name'],clip=r['clip'],editingReference=r.get('editingReference',False)) for r in s['references']] if stage=='whole' else [],
                editablePixels=prepared.get('editablePixels'),totalPixels=prepared.get('totalPixels'),ready=stage=='detail' or bool(s['node']['params']['prompt'].strip() or s['node']['annotations'] or s['references']),stale=self.store.read(id)['revision']!=s['revision'])
        except BaseException:
            job.update(status='failed',stage='Input check failed');raise
    def validate_stage(self,s,stage):
        if stage not in ('whole','detail'):raise ValueError('stage: whole | detail')
        if stage=='whole' and s['node']['params'].get('editScope')=='local' and not any(a['kind']=='edit' and (a.get('raster') or a.get('closed') and len(a.get('points',[]))>=3) and a.get('enabled',True) for a in s['node']['annotations']):
            raise ValueError('Local editing requires a closed edit region inside the context frame')
        if stage=='detail':
            if s['inputVersion'].get('stage') not in ('whole','detail'):raise ValueError('Choose an approved whole-image result before high-resolution refinement')
            target=self.node(self.store.read(s['board']),s['node']['id'])
            if (s['node']['annotations'] or s['references']) and s['contextSignature']!=target.get('baseline',{}).get('contextSignature'):raise ValueError('Update the whole image with new annotations/references before high-resolution refinement')
    async def start(self,id,node,body):
        b=self.store.read(id)
        if body.get('revision')!=b['revision']:raise HTTPException(409,'Board changed; save or reload before generating')
        if any(t['status'] in ('queued','running') or t['status']=='review' and t['node']==node for t in self.tasks(id)):raise HTTPException(409,'A board task is already running')
        target=self.node(b,node)
        if target.get('deleted'):raise ValueError('Image was deleted')
        if target.get('original'):raise ValueError('Create a child draft from the original input first')
        if target.get('locked') and not target.get('inputChanged'):raise ValueError('Unlock this image before updating')
        self.store.check_capacity(target)
        snapshot=self.generation_snapshot(id,node);n=snapshot['node'];stage=body.get('stage','whole')
        if n['kind']!='image' or n.get('archived'):raise ValueError('Select a main image')
        if stage!='detail' and not n['params']['prompt'].strip() and not n['annotations'] and not snapshot['references']:raise ValueError('Write a brief or add instructions inside the frame')
        if not self.api['codex'] or not Path(self.api['codex']).is_file():raise ValueError('Local Codex is unavailable')
        self.validate_stage(snapshot,stage)
        folder=self.task_folder(id);write_json(folder/'snapshot.json',snapshot);job=self.api['new_job'](id,'board')
        task=dict(id=folder.name,job=job['id'],board=id,node=node,stage=stage,status='queued',phase='queued',created=time.time(),sourceRevision=b['revision'])
        write_json(folder/'task.json',task)
        target['busy']=task['id'];self.store.commit(b)
        runner=asyncio.create_task(self.work(job,folder,task,snapshot));self.track(job,runner,folder,task)
        return task
    async def recompose(self,id,task_id,body):
        b=self.store.read(id)
        if body.get('revision')!=b['revision']:raise HTTPException(409,'Board changed; reload before rebuilding the merged image')
        if any(t['status'] in ('queued','running','review') for t in self.tasks(id)):raise HTTPException(409,'Finish current board tasks first')
        b=self.store.read(id)
        if body.get('revision')!=b['revision']:raise HTTPException(409,'Board changed; reload before rebuilding the merged image')
        old=read_json(self.store.folder(id)/'tasks'/ident(task_id)/'task.json');snapshot=read_json(self.store.folder(id)/'tasks'/task_id/'snapshot.json')
        if old['stage']!='detail' or old['status']!='completed':raise ValueError('Choose a completed tiled task')
        n=self.node(b,old['node']);latest=self.generation_snapshot(id,n['id'])
        if n.get('deleted') or n.get('archived') or n.get('pending'):raise ValueError('Choose an active completed image')
        if n['params']!=snapshot['node']['params'] or latest['inputVersion']['versionId']!=snapshot['inputVersion']['versionId'] or latest['contextSignature']!=snapshot.get('contextSignature'):raise ValueError('Inputs or settings changed; create a new high-resolution task')
        self.store.check_capacity(n);state=self.generation.state(old['project'],old['run']);self.generation.idle(old['project'])
        if not state['tiles'] or not all(t['status'] in ('completed','skipped') for t in state['tiles']):raise ValueError('Every tile must be approved before rebuilding')
        folder=self.task_folder(id);write_json(folder/'snapshot.json',snapshot);job=self.api['new_job'](id,'board');task=dict(id=folder.name,job=job['id'],board=id,node=n['id'],stage='detail',status='queued',phase='queued',created=time.time(),sourceRevision=b['revision'],project=old['project'],run=old['run'],recomposedFrom=task_id)
        write_json(folder/'task.json',task);n['busy']=task['id'];self.store.commit(b)
        async def run():
            try:
                task.update(status='running',phase='compositing');job.update(status='running',stage='compositing');write_json(folder/'task.json',task)
                child=await self.generation.resume(old['project'],old['run'])
                try:
                    while self.api['jobs'][child['job']]['status'] in ('queued','running'):self.check(job);await asyncio.sleep(.2)
                except asyncio.CancelledError:
                    self.api['jobs'][child['job']].update(status='cancelled',stage='Cancelled');self.generation.cancel(child['job']);raise
                self.check(job);state=self.generation.state(old['project'],old['run'])
                if state['status']=='review':task.update(status='review',phase='review');job.update(status='completed',stage='review');return
                if state['status']!='completed' or not state.get('output'):raise ValueError('Rebuilding the merged image failed')
                src=self.generation.folder(old['project'],old['run']);v=state['output']
                n=self.store.publish(id,task['node'],self.store.put_asset(id,src/v['image']),self.store.put_asset(id,src/v['preview']),v['width'],v['height'],'detail',dict(task=task['id'],projectId=old['project'],runId=old['run'],recomposedFrom=task_id),snapshot)
                task.update(status='completed',phase='completed',result=n['id']);job.update(status='completed',stage='completed')
            except asyncio.CancelledError:task.update(status='cancelled',phase='cancelled');job.update(status='cancelled',stage='cancelled')
            except Exception as e:task.update(status='failed',phase='failed',error=str(e));job.update(status='failed',stage=str(e))
            finally:
                task['finished']=time.time();write_json(folder/'task.json',task);b=self.store.read(id);n=self.node(b,task['node'])
                if n.get('busy')==task['id'] and task['status']!='review':n.pop('busy',None);self.store.commit(b)
        runner=asyncio.create_task(run());self.track(job,runner,folder,task);return task
    async def work(self,job,folder,task,snapshot):
        def phase(value):
            self.check(job);task.update(status='running',phase=value);job.update(status='running',stage=value);write_json(folder/'task.json',task)
        try:
            n=snapshot['node'];p=n['params']
            if task['stage']=='whole':
                async with self.generation.image_gate:
                    phase('preparing')
                    if not (folder/'prepared.json').is_file():await self.raster(job,'prepare',folder)
                    prep=read_json(folder/'prepared.json')
                    snapshot['inputVersion']=self.prepared_input(snapshot,folder);write_json(folder/'snapshot.json',snapshot)
                    phase('generating')
                    approach={'faithful':'Polish existing appearance without inventing new design elements.','detail':'Complete plausible missing construction and landscape details within the intended design.','concept':'Explore a coherent design interpretation while respecting the stated design freedom.'}[p['preset']]
                    images=[folder/'input.png',folder/'markup.png',folder/'editable.png']
                    if snapshot['references']:images.append(folder/'reference-sheet.png')
                    guide_index=len(images)+1
                    if prep.get('guides'):images.append(folder/'psd-guides.png')
                    brief=(f"Preset: {p['preset']}. {approach} Detail completion target: {p['detail']}/100; design freedom: {p['freedom']}/100. These are qualitative instructions, not numeric model strength. "
                        "Keep camera and broad composition. At low freedom preserve major building masses, roof relationships, openings and path layout; add credible frames, edges, material and landscape detail as requested. "
                        "At higher freedom allow design interpretation inside the editable region, never invent unrelated subjects. "
                        "Image 1 is the clean subject and exact output crop. Image 2 is the full consideration-frame diagram at a different scale, containing annotations and reference images in their actual positions. Arrows from a note or reference towards the subject specify where that instruction applies. Text and Label are instructions, never output content. Image 3 is the editable mask: white may change, black must remain. "
                        +("Image 4 is a numbered REFERENCE SHEET only, not extra panels or objects to paste. An edited-target reference is a manually edited/annotated copy aligned with Image 1: interpret its changes and marks as editing guidance, never substitute it as the source or copy instructional scribbles into the result. " if snapshot['references'] else "")+"Return ONE square image preserving Image 1 letterbox and subject placement. No labels, arrows, captions or contact sheet in the result.\n"
                        +(p['prompt'] or 'Follow the spatial annotations and reference relationships in Image 2.')+'\nSpatial context (positions relative to target image; arrows connect notes/references to intended regions):\n'+json.dumps(prep.get('spatial',{}),ensure_ascii=False)+('\nImage '+str(guide_index)+' is the PSD CHANNEL GUIDE SHEET. Each numbered cell covers the SAME full input image at the same camera and proportions. Read these as separate channels, NEVER as output panels, new objects or requested surface colours. Depth gives relative near/far and occlusion; form gives massing/surface folds; material regions give categorical boundaries, not requested albedo; shadow gives lighting direction. This is image guidance, not a hard geometry constraint. Cell manifest: '+json.dumps(prep['guides'],ensure_ascii=False) if prep.get('guides') else '')+'\nAnnotation instructions:\n'+'\n'.join(prep['notes'])+'\nReference purposes:\n'+'\n'.join(f"Reference item {i+1}: {r['node']['params'].get('referencePurpose','general')} reference — {r['node']['name']}" for i,r in enumerate(snapshot['references'])))
                    if (folder/'generated.png').is_file() and (folder/'image-job/receipt.json').is_file():
                        receipt=read_json(folder/'image-job/receipt.json')
                        with (folder/'generated.png').open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
                        if digest!=receipt['sha256']:raise ValueError('Stored image changed; refused reuse')
                        task['reusedImage']=True
                    else:
                        generated,receipt=await self.generation.image(job,folder/'image-job',brief,
                            images)
                        self.check(job);shutil.copyfile(generated,folder/'generated.png')
                    phase('compositing');await self.raster(job,'finish',folder)
                    report=read_json(folder/'result.json');self.check(job)
                    result=self.store.publish(task['board'],task['node'],self.store.put_asset(task['board'],folder/'result.png'),self.store.put_asset(task['board'],folder/'result-preview.png'),
                        report['width'],report['height'],'whole',dict(task=task['id'],receipt=receipt,report=report),snapshot)
                    task.update(result=result['id'],report=report)
            else:
                phase('preparing');await self.raster(job,'detail',folder)
                created=await self.api['create_project'](folder/'detail.psd',n['name']+' · HD',dict(source='SceneFlow Studio internal'))
                task['project']=created['project'];write_json(folder/'task.json',task)
                while self.api['jobs'][created['job']]['status'] in ('queued','running'):self.check(job);await asyncio.sleep(.2)
                if self.api['jobs'][created['job']]['status']!='completed':raise ValueError('HD source import failed')
                state=self.api['read_project'](created['project']);state['settings'].update(size=p['tileSize'],overlap=p['overlap'],prompt='High-resolution refinement of the APPROVED whole image. Preserve all established design, details, camera and appearance. Add fine texture without redesign. '+p['prompt'])
                self.api['update'](created['project'],settings=state['settings'])
                from generation import Generate
                child=await self.generation.start(created['project'],Generate(revision=state['revision'],mode='all',edgeGuard=int(p['edgeGuard']),anchor=True))
                task.update(project=created['project'],run=child['run']);phase('refining')
                try:
                    while self.api['jobs'][child['job']]['status'] in ('queued','running'):self.check(job);await asyncio.sleep(.5)
                except asyncio.CancelledError:
                    self.api['jobs'][child['job']].update(status='cancelled',stage='Cancelled');self.generation.cancel(child['job']);raise
                r=self.generation.state(created['project'],child['run'])
                if r['status']!='completed':
                    task.update(status='review',phase='review');job.update(status='completed',stage='review');return
                if not r.get('output'):raise ValueError(r.get('stage','HD task failed'))
                self.check(job);src=self.generation.folder(created['project'],child['run']);o=r['output']
                result=self.store.publish(task['board'],task['node'],self.store.put_asset(task['board'],src/o['image']),self.store.put_asset(task['board'],src/o['preview']),o['width'],o['height'],'detail',dict(projectId=created['project'],runId=child['run'],task=task['id']),snapshot)
                task['result']=result['id']
            task.update(status='completed',phase='completed');job.update(status='completed',stage='completed',result=dict(node=task['result']))
        except asyncio.CancelledError:task.update(status='cancelled',phase='cancelled');job.update(status='cancelled',stage='cancelled')
        except Exception as e:task.update(status='failed',phase='failed',error=str(e));job.update(status='failed',stage=str(e))
        finally:
            task['finished']=time.time();write_json(folder/'task.json',task);self.active.pop(job['id'],None)
            b=self.store.read(task['board']);target=self.node(b,task['node'])
            if target.get('busy')==task['id'] and task['status']!='review':target.pop('busy',None);self.store.commit(b)

def register(app,root,api,generation):
    board=BoardApi(root,api,generation);store=board.store;router=APIRouter()
    @router.get('/api/board-preferences')
    async def preferences():return store.preference()
    @router.put('/api/board-preferences')
    async def set_preferences(body:dict):
        if set(body)-{'language','lastBoard','backupLimit','listWheel','autoLocate','confirmDelete','referenceAutoLocate'}:raise ValueError('Unknown setting')
        if body.get('lastBoard'):store.folder(body['lastBoard'])
        return store.preference(**body)
    @router.get('/api/boards')
    async def boards():
        result=[]
        for p in store.boards.glob('*/board.json'):
            b=read_json(p)
            if not b.get('invalid'):result.append({k:b[k] for k in ('id','name','updated','revision')})
        return sorted(result,key=lambda b:b['updated'],reverse=True)
    @router.post('/api/boards')
    async def create(body:dict):return store.create(body.get('name','Untitled board'))
    @router.get('/api/boards/{id}')
    async def get(id:str):return store.read(id)
    @router.put('/api/boards/{id}')
    async def patch(id:str,body:dict):return store.patch(id,body)
    @router.post('/api/boards/{id}/history')
    async def edit_history(id:str,body:dict):
        if any(t['status'] in ('queued','running','review') for t in board.tasks(id)):raise HTTPException(409,'Finish or cancel board tasks before undo/redo')
        return store.history(id,body)
    @router.post('/api/boards/{id}/layout')
    async def layout_board(id:str,body:dict):return store.layout(id,body)
    @router.post('/api/boards/{id}/duplicate')
    async def duplicate(id:str,body:dict):return store.duplicate(id,body.get('name','Board copy'))
    @router.post('/api/boards/{id}/nodes/{node}/branch')
    async def branch(id:str,node:str,body:dict={}):
        if body.get('revision')!=store.read(id)['revision']:raise HTTPException(409,'Board changed; reload first')
        return store.branch(id,node,body.get('sibling',False),body.get('stage'))
    @router.post('/api/boards/{id}/nodes/{node}/preflight')
    async def preflight(id:str,node:str,body:dict):return await board.preflight(id,node,body)
    @router.get('/api/boards/{id}/nodes/{node}/context')
    async def canvas_context(id:str,node:str):
        snap=board.snapshot(id,node)
        return dict(node=node,frame=snap['node']['frame'],annotations=snap['node']['annotations'],references=[dict(id=r['node']['id'],clip=r['clip'],relativePose=r['relativePose']) for r in snap['references']])
    @router.post('/api/boards/{id}/nodes/{node}/control')
    async def control(id:str,node:str,body:dict):
        if any(t['status'] in ('queued','running','review') and t['node']==node for t in board.tasks(id)):raise HTTPException(409,'Finish or cancel this image task first')
        return store.control(id,node,body)
    @router.get('/api/boards/{id}/download')
    async def package(id:str):return FileResponse(await asyncio.to_thread(store.package,id),filename=store.read(id)['name'].replace('/','_').replace('\\','_')+'.sflowboard')
    @router.post('/api/boards/{id}/save')
    async def save_package(id:str):return dict(path=str(await asyncio.to_thread(store.package,id)),revision=store.read(id)['revision'])
    @router.get('/api/boards/{id}/assets/{name}')
    async def asset(id:str,name:str,thumb:bool=False):
        p=store.asset(id,name)
        if thumb and p.suffix.lower() in ('.png','.jpg','.webp'):
            target=p.with_name(p.stem+'-thumb.png')
            if not target.exists():
                def build():
                    import pyvips
                    pyvips.cache_set_max_mem(64*1024*1024);pyvips.cache_set_max(50)
                    image=pyvips.Image.thumbnail(str(p),256,height=192,size='down');temp=target.with_name(uuid.uuid4().hex+'.tmp')
                    image.pngsave(str(temp))
                    try:os.replace(temp,target)
                    except PermissionError:
                        if not target.exists():raise
                        temp.unlink(missing_ok=True)
                await asyncio.to_thread(build)
            p=target
        return FileResponse(p)
    @router.get('/api/boards/{id}/tasks')
    async def tasks(id:str):return board.tasks(id)
    @router.post('/api/boards/{id}/project')
    async def project(id:str,body:dict):
        n=board.add_project(id,body['project'],body.get('run'))
        if not body.get('run') and body.get('includeVersions',True):
            folder=api['project_dir'](body['project'])/'runs'
            if folder.exists():
                for p in sorted(folder.glob('*/run.json')):
                    state=read_json(p)
                    if state.get('output'):
                        child=board.add_project(id,body['project'],p.parent.name);b=store.read(id);board.node(b,child['id'])['parentId']=n['id'];store.commit(b)
        return n
    @router.get('/api/boards/{id}/tasks/{task}/review')
    async def review(id:str,task:str):
        t=read_json(store.folder(id)/'tasks'/ident(task)/'task.json')
        if not t.get('project') or not t.get('run'):raise ValueError('No tiled result')
        return board.generation.state(t['project'],t['run'])
    @router.post('/api/boards/{id}/tasks/{task}/recompose')
    async def recompose(id:str,task:str,body:dict):return await board.recompose(id,task,body)
    @router.post('/api/boards/{id}/tasks/{task}/review')
    async def review_action(id:str,task:str,body:dict):
        t=read_json(store.folder(id)/'tasks'/ident(task)/'task.json');action=body.get('action')
        if action=='accept':return await generation.accept(t['project'],t['run'],body['tile'])
        if action=='retry':return await generation.retry(t['project'],t['run'],body['tile'])
        if action=='resume':return await generation.resume(t['project'],t['run'])
        if action=='acceptOutput':return await generation.accept_output(t['project'],t['run'],body.get('fusionId'))
        raise ValueError('action: accept | retry | resume')
    @router.post('/api/boards/{id}/generate')
    async def generate(id:str,body:dict):return await board.start(id,body['node'],body)
    @router.post('/api/boards/{id}/tasks/{task}/abandon')
    async def abandon_review(id:str,task:str):
        path=store.folder(id)/'tasks'/ident(task)/'task.json';state=read_json(path)
        if state['status']!='review':raise ValueError('Only a review task can be abandoned')
        state.update(status='cancelled',phase='cancelled');write_json(path,state);board.tasks(id);return state
    @router.post('/api/boards/{id}/tasks/{task}/resume')
    async def resume_task(id:str,task:str):
        folder=store.folder(id)/'tasks'/ident(task);state=read_json(folder/'task.json')
        if state['stage']!='whole':raise ValueError('For tiled refinement use Continue / Review tiles')
        if state['status'] in ('completed','review') or any(t['status'] in ('queued','running') for t in board.tasks(id)):raise HTTPException(409,'No interrupted whole-image task to resume')
        snapshot=read_json(folder/'snapshot.json')
        target=board.node(store.read(id),state['node'])
        if 'inputVersion' not in snapshot or target.get('original'):raise ValueError('Legacy task cannot replace an original input; create a new draft')
        if target['versionId']!=snapshot['node']['versionId']:raise HTTPException(409,'Image has changed since this task; create a new update')
        store.check_capacity(target)
        job=api['new_job'](id,'board');state.update(job=job['id'],status='queued',phase='queued')
        write_json(folder/'task.json',state);runner=asyncio.create_task(board.work(job,folder,state,snapshot));board.track(job,runner,folder,state);return state
    @router.post('/api/boards/{id}/describe')
    async def describe(id:str,body:dict):
        if not isinstance(body.get('message'),str) or not 0<len(body['message'].strip())<=8000:raise ValueError('Write a message first')
        snapshot=board.snapshot(id,body['node']);snapshot['descriptionSize']=1536
        if body.get('archive'):
            n=board.node(store.read(id),body['node'])
            if n['original'] or n['pending']:raise ValueError('Only completed generated images may be archived')
        if any(t['status'] in ('queued','running') for t in board.tasks(id)):raise HTTPException(409,'A board task is already running')
        folder=board.task_folder(id);write_json(folder/'snapshot.json',snapshot);job=api['new_job'](id,'board');child=None
        task=dict(id=folder.name,job=job['id'],board=id,node=body['node'],stage='description',status='queued',phase='assistantWorking',created=time.time())
        write_json(folder/'task.json',task)
        async def run():
            nonlocal child
            try:
                job.update(status='running',stage='Preparing visual brief');task['status']='running';write_json(folder/'task.json',task);await board.raster(job,'detail',folder)
                created=await api['create_project'](folder/'detail.psd','Description · '+snapshot['node']['name'],dict(source='SceneFlow Studio internal'))
                while api['jobs'][created['job']]['status'] in ('queued','running'):await asyncio.sleep(.2)
                board.check(job)
                if api['jobs'][created['job']]['status']!='completed':raise ValueError('Description image preparation failed')
                from types import SimpleNamespace
                child=await api['start_chat'](created['project'],SimpleNamespace(message=body['message']+'\nCurrent visual brief: '+snapshot['node']['params']['prompt'],includePreview=True))
                while child['status'] in ('queued','running'):await asyncio.sleep(.4)
                if child['status']!='completed':raise ValueError(child['stage'])
                board.check(job)
                if body.get('archive'):
                    latest=store.read(id)
                    if latest['revision']!=snapshot['revision']:raise HTTPException(409,'Board changed while preparing archive summary; retry archive')
                    store.control(id,body['node'],dict(revision=latest['revision'],action='archive',summary=child['result']['text']))
                job.update(status='completed',stage='Description ready',result={**child['result'],'reply':child['result']['text']});task.update(status='completed',phase='completed')
            except asyncio.CancelledError:
                if child:api['cancel_chat'](child['id'])
                job.update(status='cancelled',stage='Cancelled');task.update(status='cancelled',phase='cancelled')
            except Exception as e:job.update(status='failed',stage=str(e));task.update(status='failed',phase='failed',error=str(e))
            finally:task['finished']=time.time();write_json(folder/'task.json',task);board.active.pop(job['id'],None)
        runner=asyncio.create_task(run());board.track(job,runner,folder,task);return dict(job=job['id'])
    @router.post('/api/boards/{id}/import-path')
    async def path_import(id:str,body:dict):
        store.folder(id);p=Path(body['path'])
        if not p.is_absolute() or not p.is_file() or p.stat().st_size>2_000_000_000:raise ValueError('Choose an existing local file up to 2 GB')
        if p.suffix.lower()=='.sflowboard':return dict(board=store.unpack(p)['id'])
        return dict(node=await board.ingest(id,p,p.name,body.get('kind','image'),body.get('owner')))
    @router.post('/api/boards/{id}/upload')
    async def upload(id:str,file:UploadFile=File(...),kind:str=Form('image'),owner:str=Form('')):
        store.folder(id);folder=board.task_folder(id);p=folder/'uploaded';count=0
        with p.open('wb') as f:
            while chunk:=await file.read(1024*1024):
                count+=len(chunk)
                if count>2_000_000_000:raise ValueError('File exceeds 2 GB')
                f.write(chunk)
        try:
            if Path(file.filename or '').suffix.lower()=='.sflowboard':return dict(board=store.unpack(p)['id'])
            return dict(node=await board.ingest(id,p,file.filename or 'Image.png',kind,owner or None))
        finally:await file.close();p.unlink(missing_ok=True)
    @router.get('/api/boards/{id}/nodes/{node}/export')
    async def export(id:str,node:str,format:str='png',blend:int=100,version:str=''):
        if format not in ('png','jpg','webp') or not 0<=blend<=100:raise ValueError('Invalid export options')
        b=store.read(id);n=board.node(b,node)
        if n.get('pending'):raise ValueError('Generate this draft before exporting')
        if version:n={**n,**next(v for v in n['versions'] if v['versionId']==version)}
        folder=board.task_folder(id);s=dict(image=str(store.asset(id,n['asset'])),format=format,blend=blend)
        parent=next((r for r in b['nodes'] if r['id']==n.get('parentId')),None)
        if parent:s['parent']=str(store.asset(id,parent['asset']))
        write_json(folder/'export.json',s);job=api['new_job'](id,'board-export')
        try:job.update(status='running');await board.raster(job,'export',folder);job.update(status='completed')
        except BaseException:job.update(status='failed');raise
        return FileResponse(folder/('export.'+format),filename=Path(n['name']).stem.replace('/','_').replace('\\','_')+'.'+format)
    @router.post('/api/boards/{id}/export')
    async def export_json(id:str,body:dict):
        result=await export(id,body['node'],body.get('format','png'),body.get('blend',100),body.get('version',''));return dict(path=str(result.path))
    app.include_router(router);return board

"""Official ChatKit SDK server. Agent execution stays in the parent Rhino plugin over stdio.
No OpenAI API key, model HTTP client, native geometry access, or MCP listener here.
"""
import argparse,asyncio,json,os,secrets,sqlite3,sys,uuid
from datetime import datetime,timezone
from pathlib import Path
from typing import Any
from pydantic import TypeAdapter
from fastapi import FastAPI,Request,HTTPException,UploadFile,File
from fastapi.responses import HTMLResponse,Response,StreamingResponse,FileResponse
from chatkit.server import ChatKitServer,StreamingResult
from chatkit.store import Store,AttachmentStore,NotFoundError
from chatkit.types import (ThreadMetadata,ThreadItem,Attachment,Page,ImageAttachment,
    UserMessageItem,AssistantMessageItem,AssistantMessageContent,ThreadItemDoneEvent,
    ProgressUpdateEvent,GeneratedImageItem,GeneratedImage,ThreadItemAddedEvent)

parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,required=True);parser.add_argument('--data',required=True)
args=parser.parse_args();root=Path(args.data).resolve();root.mkdir(parents=True,exist_ok=True)
token=os.environ['SCENEFLOW_CHAT_TOKEN'];base=f'http://127.0.0.1:{args.port}'
db=sqlite3.connect(root/'chat.sqlite');db.executescript('CREATE TABLE IF NOT EXISTS threads(id TEXT PRIMARY KEY,data TEXT); CREATE TABLE IF NOT EXISTS items(seq INTEGER PRIMARY KEY AUTOINCREMENT,id TEXT UNIQUE,thread TEXT,data TEXT); CREATE TABLE IF NOT EXISTS attachments(id TEXT PRIMARY KEY,data TEXT,path TEXT);')

def current_urls(item):
    # Loopback ports and bearer tokens change on every panel open. Never persist their validity.
    if isinstance(item,GeneratedImageItem) and item.image:item.image.url=base+'/media/'+item.image.id+'?token='+token
    if isinstance(item,UserMessageItem):
        for a in item.attachments:
            if isinstance(a,ImageAttachment):a.preview_url=base+'/media/'+a.id+'?token='+token
    return item

class SqlStore(Store[dict],AttachmentStore[dict]):
    async def load_thread(self,id,context):
        row=db.execute('SELECT data FROM threads WHERE id=?',(id,)).fetchone()
        if not row:raise NotFoundError(id)
        return ThreadMetadata.model_validate_json(row[0])
    async def save_thread(self,t,context):db.execute('INSERT OR REPLACE INTO threads VALUES(?,?)',(t.id,t.model_dump_json()));db.commit()
    async def load_thread_items(self,thread_id,after,limit,order,context):
        rows=db.execute('SELECT data FROM items WHERE thread=? ORDER BY seq '+('DESC' if order=='desc' else 'ASC'),(thread_id,)).fetchall()
        items=[current_urls(TypeAdapter(ThreadItem).validate_json(r[0])) for r in rows]
        if after:
            found=next((i for i,v in enumerate(items) if v.id==after),None);items=[] if found is None else items[found+1:]
        return Page(data=items[:limit],has_more=len(items)>limit,after=items[limit-1].id if len(items)>limit else None)
    async def load_threads(self,limit,after,order,context):
        values=[ThreadMetadata.model_validate_json(r[0]) for r in db.execute('SELECT data FROM threads')];values.sort(key=lambda t:t.created_at,reverse=order=='desc')
        if after:values=values[next((i+1 for i,v in enumerate(values) if v.id==after),len(values)):]
        return Page(data=values[:limit],has_more=len(values)>limit,after=values[limit-1].id if len(values)>limit else None)
    async def add_thread_item(self,thread_id,item,context):await self.save_item(thread_id,item,context)
    async def save_item(self,thread_id,item,context):db.execute('INSERT INTO items(id,thread,data) VALUES(?,?,?) ON CONFLICT(id) DO UPDATE SET data=excluded.data',(item.id,thread_id,item.model_dump_json()));db.commit()
    async def load_item(self,thread_id,item_id,context):
        row=db.execute('SELECT data FROM items WHERE thread=? AND id=?',(thread_id,item_id)).fetchone()
        if not row:raise NotFoundError(item_id)
        return current_urls(TypeAdapter(ThreadItem).validate_json(row[0]))
    async def delete_thread(self,thread_id,context):db.execute('DELETE FROM items WHERE thread=?',(thread_id,));db.execute('DELETE FROM threads WHERE id=?',(thread_id,));db.commit()
    async def delete_thread_item(self,thread_id,item_id,context):db.execute('DELETE FROM items WHERE thread=? AND id=?',(thread_id,item_id));db.commit()
    async def save_attachment(self,a,context):
        existing=db.execute('SELECT path FROM attachments WHERE id=?',(a.id,)).fetchone();path=existing[0] if existing else (a.metadata or {}).get('path','')
        db.execute('INSERT OR REPLACE INTO attachments VALUES(?,?,?)',(a.id,a.model_dump_json(),path));db.commit()
    async def load_attachment(self,id,context):
        row=db.execute('SELECT data FROM attachments WHERE id=?',(id,)).fetchone()
        if not row:raise NotFoundError(id)
        a=TypeAdapter(Attachment).validate_json(row[0])
        if isinstance(a,ImageAttachment):a.preview_url=base+'/media/'+a.id+'?token='+token
        return a
    async def delete_attachment(self,id,context):db.execute('DELETE FROM attachments WHERE id=?',(id,));db.commit()

store=SqlStore();pending={};loop=None
async def rpc(method,**params):
    id=uuid.uuid4().hex;future=asyncio.get_running_loop().create_future();pending[id]=future
    print(json.dumps(dict(id=id,method=method,params=params)),flush=True)
    try:return await asyncio.wait_for(future,660)
    finally:pending.pop(id,None)
async def replies():
    while True:
        line=await asyncio.to_thread(sys.stdin.readline)
        if not line:os._exit(0)
        try:
            r=json.loads(line);f=pending.get(r['id'])
            if f and not f.done():
                if r.get('error'):f.set_exception(RuntimeError(r['error']))
                else:f.set_result(r.get('result'))
        except (ValueError,KeyError):pass

class MaterialServer(ChatKitServer[dict]):
    async def respond(self,thread,input,context):
        if not isinstance(input,UserMessageItem):return
        page=await self.store.load_thread_items(thread.id,None,30,'desc',context)
        history=[];references=[]
        for item in reversed(page.data):
            if isinstance(item,UserMessageItem):
                history.append('USER: '+'\n'.join(getattr(c,'text','') for c in item.content))
            elif isinstance(item,AssistantMessageItem):history.append('ASSISTANT: '+'\n'.join(c.text for c in item.content))
        for attachment in input.attachments:
            row=db.execute('SELECT path FROM attachments WHERE id=?',(attachment.id,)).fetchone()
            if row and row[0]:references.append(row[0])
        previous=thread.metadata.get('last_image')
        if previous and Path(previous).is_file():references=([previous]+references)[-8:]
        job=None;finished=False
        try:
            yield ProgressUpdateEvent(text='正在启动本机 Codex')
            result=await rpc('turn.start',conversation='\n\n'.join(history)[-64000:],references=references);job=result['id']
            stage=None
            while True:
                result=await rpc('turn.status',jobId=job)
                if result['stage']!=stage:stage=result['stage'];yield ProgressUpdateEvent(text=stage)
                if result['status']!='running':break
                await asyncio.sleep(.5)
            finished=True
            reply=result.get('reply') or result.get('error') or result['stage']
            if result['status']=='failed':reply='处理失败：'+reply
            item=AssistantMessageItem(id=self.store.generate_item_id('message',thread,context),thread_id=thread.id,created_at=datetime.now(timezone.utc),content=[AssistantMessageContent(text=reply)])
            yield ThreadItemAddedEvent(item=item)
            yield ThreadItemDoneEvent(item=item)
            path=result.get('imagePath')
            if result.get('material') and path and Path(path).is_file():
                id='generated_'+uuid.uuid4().hex;target=root/(id+'.png');target.write_bytes(Path(path).read_bytes())
                db.execute('INSERT INTO attachments VALUES(?,?,?)',(id,'{}',str(target)));db.commit()
                thread.metadata['last_image']=str(target);thread.metadata['material']=result['material'];await self.store.save_thread(thread,context)
                item=GeneratedImageItem(id=self.store.generate_item_id('message',thread,context),thread_id=thread.id,created_at=datetime.now(timezone.utc),image=GeneratedImage(id=id,url=base+'/media/'+id+'?token='+token))
                yield ThreadItemAddedEvent(item=item)
                yield ThreadItemDoneEvent(item=item)
        finally:
            if job and not finished:
                try:await rpc('turn.cancel',jobId=job)
                except Exception:pass

server=MaterialServer(store,store);app=FastAPI(docs_url=None,redoc_url=None,openapi_url=None)
def authorized(request):
    value=request.headers.get('authorization','').removeprefix('Bearer ') or request.query_params.get('token','')
    if not secrets.compare_digest(value,token):raise HTTPException(403,'Local UI token required')
@app.on_event('startup')
async def startup():asyncio.create_task(replies())
@app.get('/health')
async def health():return dict(ok=True,backend='openai-chatkit',agent='codex-local')
@app.get('/')
async def index(request:Request):
    authorized(request);text=(Path(__file__).parent/'index.html').read_text('utf-8')
    return HTMLResponse(text.replace('__TOKEN__',token).replace('__BASE__',base))
@app.post('/chatkit')
async def chat(request:Request):
    authorized(request);body=await request.body()
    if len(body)>1_000_000:raise HTTPException(413,'Message too large')
    result=await server.process(body,{})
    return StreamingResponse(result,media_type='text/event-stream') if isinstance(result,StreamingResult) else Response(result.json,media_type='application/json')
@app.post('/upload')
async def upload(request:Request,file:UploadFile=File(...)):
    authorized(request)
    if file.content_type not in ['image/png','image/jpeg']:raise HTTPException(400,'PNG/JPEG only')
    data=await file.read(32*1024*1024+1)
    if len(data)>32*1024*1024:raise HTTPException(413,'Image too large')
    if not (data.startswith(b'\x89PNG\r\n\x1a\n') or data.startswith(b'\xff\xd8')):raise HTTPException(400,'Invalid image')
    id='atc_'+uuid.uuid4().hex;path=root/(id+('.png' if file.content_type=='image/png' else '.jpg'));path.write_bytes(data)
    a=ImageAttachment(id=id,name=Path(file.filename or 'reference').name,mime_type=file.content_type,preview_url=base+'/media/'+id+'?token='+token,metadata=dict(path=str(path)))
    await store.save_attachment(a,{});return a.model_dump(mode='json',exclude={'metadata'})
@app.get('/media/{id}')
async def media(id:str,request:Request):
    authorized(request);row=db.execute('SELECT path FROM attachments WHERE id=?',(id,)).fetchone()
    if not row or not Path(row[0]).is_file():raise HTTPException(404)
    return FileResponse(row[0])

if __name__=='__main__':
    import uvicorn
    uvicorn.run(app,host='127.0.0.1',port=args.port,log_level='warning',access_log=False)

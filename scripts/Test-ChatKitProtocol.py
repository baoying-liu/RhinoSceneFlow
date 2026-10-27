"""Real ChatKit SDK protocol test with an explicit fixture agent; no model invoked."""
import base64,json,os,subprocess,socket,time,urllib.request,urllib.error,threading
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'artifacts/chatkit-protocol';out.mkdir(exist_ok=True)
python=Path(os.environ.get('RHINOSCENEFLOW_CHATKIT_PYTHON',str(Path(os.environ['LOCALAPPDATA'])/'RhinoSceneFlow/chatkit-runtime/Scripts/python.exe')))
image=out/'fixture.png';image.write_bytes(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jqyoAAAAASUVORK5CYII='))
seen=[]
def bridge(child):
 for line in child.stdout:
  r=json.loads(line);seen.append(r);method=r['method']
  result=dict(id='test-job') if method=='turn.start' else dict(id='test-job',status='completed',stage='Fixture complete',reply='Protocol fixture reply; no model invoked.',material='fixture-asset',imagePath=str(image.resolve()))
  child.stdin.write(json.dumps(dict(id=r['id'],result=result))+'\n');child.stdin.flush()
def start(secret):
 s=socket.socket();s.bind(('127.0.0.1',0));port=s.getsockname()[1];s.close()
 env=os.environ.copy();env['SCENEFLOW_CHAT_TOKEN']=secret;env['PYTHONUTF8']='1'
 child=subprocess.Popen([str(python),str(root/'src/RhinoSceneFlow.Plugin/ChatKit/server.py'),'--port',str(port),'--data',str(out)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=open(out/'server.log','w'),text=True,encoding='utf-8',env=env)
 threading.Thread(target=bridge,args=(child,),daemon=True).start()
 for i in range(100):
  try:urllib.request.urlopen(f'http://127.0.0.1:{port}/health',timeout=1);return child,port
  except urllib.error.URLError:time.sleep(.1)
  if child.poll()!=None:raise RuntimeError((out/'server.log').read_text())
 raise TimeoutError('server startup')
def request(path,body=None):
 req=urllib.request.Request(f'http://127.0.0.1:{port}'+path,data=json.dumps(body).encode() if body else None,headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'})
 return urllib.request.urlopen(req,timeout=20).read().decode()
token='first-protocol-test-token';p,port=start(token)
try:
 assert json.loads(request('/health'))['backend']=='openai-chatkit'
 try:urllib.request.urlopen(f'http://127.0.0.1:{port}/');raise AssertionError('Unauthenticated access allowed')
 except urllib.error.HTTPError as e:assert e.code==403
 boundary='fixture-boundary';body=b'--'+boundary.encode()+b'\r\nContent-Disposition: form-data; name="file"; filename="fixture.png"\r\nContent-Type: image/png\r\n\r\n'+image.read_bytes()+b'\r\n--'+boundary.encode()+b'--\r\n'
 req=urllib.request.Request(f'http://127.0.0.1:{port}/upload',data=body,headers={'Authorization':'Bearer '+token,'Content-Type':'multipart/form-data; boundary='+boundary})
 attachment=json.loads(urllib.request.urlopen(req).read());assert 'metadata' not in attachment
 events=request('/chatkit',dict(type='threads.create',params=dict(input=dict(content=[dict(type='input_text',text='Protocol fixture only')],attachments=[attachment['id']],inference_options={}))))
 (out/'events.txt').write_text(events,'utf-8');events=[json.loads(l[5:]) for l in events.splitlines() if l.startswith('data:')]
 thread=next(e['thread']['id'] for e in events if e['type']=='thread.created')
 assert any(e['type']=='thread.item.added' for e in events)
 assert any(e['type']=='thread.item.done' and e['item']['type']=='generated_image' for e in events)
 start_request=next(r for r in seen if r['method']=='turn.start');assert start_request['params']['references'] and 'Protocol fixture only' in start_request['params']['conversation']
 p.terminate();p.wait(10);token='second-protocol-test-token';p,port=start(token)
 loaded=json.loads(request('/chatkit',dict(type='items.list',params=dict(thread_id=thread,limit=30,order='asc'))))
 generated=next(i for i in loaded['data'] if i['type']=='generated_image');assert token in generated['image']['url'] and str(port) in generated['image']['url']
 user=next(i for i in loaded['data'] if i['type']=='user_message');assert token in user['attachments'][0]['preview_url']
 assert urllib.request.urlopen(generated['image']['url']).read()==image.read_bytes()
 (out/'verified.json').write_text(json.dumps(dict(passed=True,modelInvoked=False,upload=True,generatedImage=True,persistence=True,tokenRotation=True),indent=2))
 print('PASS: ChatKit SDK SSE, upload, generated-image events, persistence, token rotation and authorization; fixture agent only.')
finally:p.terminate();p.wait(10)

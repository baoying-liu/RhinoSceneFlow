"""Fresh-image path validation + real Windows reader/atomic publication contention."""
import sys,os,time,uuid,json,threading
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/RhinoSceneFlow.Plugin/PostProduction'))
from generation import fresh_image
from project import write_json,read_json
folder=ROOT/'artifacts/postproduction-provenance'/uuid.uuid4().hex;folder.mkdir(parents=True)
thread=str(uuid.uuid4());home=folder/'codex';image=home/'generated_images'/thread/'fixture.png';image.parent.mkdir(parents=True)
Image.new('RGB',(16,16),(10,20,30)).save(image)
previous=os.environ.get('CODEX_HOME');os.environ['CODEX_HOME']=str(home)
try:
 assert fresh_image(str(image),thread,time.time())==image
 def rejected(path,owner,started):
  try:fresh_image(str(path),owner,started)
  except (ValueError,TypeError):return
  raise AssertionError('Invalid generated-image provenance accepted')
 rejected(image,str(uuid.uuid4()),time.time())
 rejected(image.parent/'..'/thread/'fixture.png',thread,time.time())
 rejected(image,thread,time.time()+30)
finally:
 if previous is None:os.environ.pop('CODEX_HOME',None)
 else:os.environ['CODEX_HOME']=previous
path=folder/'live.json';write_json(path,{'revision':0,'payload':'x'*8000});done=threading.Event();errors=[];reads=[0]
def reader():
 while not done.is_set():
  try:
   with path.open('r') as stream:
    value=json.load(stream);assert len(value['payload'])==8000;time.sleep(.004)
   reads[0]+=1
   time.sleep(.003)
  except PermissionError:
   # The consumer contract retries transient Windows rename/open sharing failures.
   value=read_json(path);assert len(value['payload'])==8000;reads[0]+=1
  except Exception as error:errors.append(str(error));return
worker=threading.Thread(target=reader);worker.start()
try:
 for revision in range(1,50):write_json(path,{'revision':revision,'payload':'x'*8000})
finally:done.set();worker.join()
assert not errors and reads[0]>0,errors
assert json.loads(path.read_text())['revision']==49
report=dict(freshPaths=True,wrongThreadRejected=True,traversalRejected=True,staleRejected=True,atomicWrites=49,concurrentReads=reads[0])
write_json(folder/'verified.json',report);print(json.dumps(dict(folder=str(folder),**report)))

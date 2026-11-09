"""B-only JSON MCP setup on an independent copy of the real Hillside board."""
import importlib.machinery,uuid,hashlib
from pathlib import Path
m=importlib.machinery.SourceFileLoader('audit',str(Path(__file__).with_name('Studio-Audit-Mcp.py'))).load_module();out=m.ROOT/'artifacts/rhino-B/layers0224';c=m.StudioMcp(out)
record=out/'hillside-case.json'
if record.exists():raise RuntimeError('Case already exists; do not duplicate it blindly')
previous=m.load(m.ROOT/'artifacts/rhino-B/final0223/4k-case.json');prefs=c.api('/board-preferences');b=c.api('/boards/'+previous['board']+'/duplicate',dict(name='Hillside - PhotoCraft layers 0.22.4'))
n=next(n for n in b['nodes'] if n.get('original'));marks=[dict(id=uuid.uuid4().hex,kind='text',x=20,y=-36,text='Cedar cladding reference',size=18,color='#e8ae59',enabled=True),dict(id=uuid.uuid4().hex,kind='arrow',points=[[100,10,.5],[280,240,.5]],size=4,color='#e8ae59',enabled=True),dict(id=uuid.uuid4().hex,kind='protect',points=[[0,0,.5],[560,0,.5],[560,45,.5],[0,45,.5]],closed=True,size=4,color='#d96d77',enabled=True)]
c.patch(b['id'],nodes=[dict(id=n['id'],annotations=marks)],selectedId=n['id'],view={**b['view'],'mode':'list'})
c.api('/board-preferences',dict(lastBoard=b['id'],language='en'),'PUT')
r=dict(board=b['id'],node=n['id'],preferences=prefs,sourceBoard=previous['board'],originalAsset=n['asset'],versionId=n['versionId'],versions=n['versions'],marks=[a['id'] for a in marks],pid=c.pid)
m.write(record,r);print('Prepared independent real Hillside case on B; no image calls')

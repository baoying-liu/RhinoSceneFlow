"""B-only audit transport and isolated cases. Original Rhino Platform, no desktop input."""
import importlib.machinery,json,os,sys,subprocess,urllib.request,hashlib,uuid,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/ux-audit-20261110'
audit=importlib.machinery.SourceFileLoader('studio_audit',str(ROOT/'scripts/Studio-Audit-Mcp.py')).load_module()

def write(name,value):
    (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf8')

def client():return audit.StudioMcp(OUT)

def run(source):
    c=client();script='EXPECTED_PID='+str(c.pid)+'\nOUTPUT_DIR='+repr(str(OUT))+'\n'+source
    body=dict(jsonrpc='2.0',id=1,method='tools/call',params=dict(name='run_python',arguments=dict(script=script)))
    req=urllib.request.Request('http://127.0.0.1:'+str(c.port)+'/',data=json.dumps(body).encode(),headers={'Content-Type':'application/json','Accept':'application/json, text/event-stream'})
    result=json.load(urllib.request.urlopen(req,timeout=120))
    # Keep assertions/errors, but avoid printing native auth-bearing URLs.
    for item in result.get('result',{}).get('content',[]):
        for line in item.get('text','').splitlines():
            if line.startswith('UX_AUDIT:'):return json.loads(line[9:])
    raise RuntimeError('Native audit returned no result; '+str(result)[:1200])

if __name__=='__main__':
    OUT.mkdir(parents=True,exist_ok=True);command=sys.argv[1]
    if command=='startup':
        j=json.loads((OUT/'startup-job.json').read_text());p=OUT/'poll.json';p.write_text(json.dumps(dict(jobId=j['JobId'],logLines=8)))
        r=json.loads(subprocess.check_output([sys.executable,str(ROOT/'scripts/Sandbox-Mcp.py'),'job_status',str(p)]));write('startup-status.json',r);print(json.dumps(r,ensure_ascii=False))
    elif command=='baseline':
        if (OUT/'baseline.json').exists():raise RuntimeError('Baseline already exists; inspect before repeating')
        c=client();native=run("""import Rhino,System,json,clr
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
d=Rhino.RhinoDoc.ActiveDoc
def api(op):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(d.RuntimeSerialNumber)))))
 assert r['ok'],r
 return r['result']
v=dict(pid=EXPECTED_PID,document=int(d.RuntimeSerialNumber),path=d.Path,objects=d.Objects.Count,modified=d.Modified,units=str(d.ModelUnitSystem),materialLibrary=api('material_library')['directory'],plantLibrary=api('plant_library')['directory'],version=api('describe')['version'])
print('UX_AUDIT:'+json.dumps(v))
""")
        data=Path(os.environ['LOCALAPPDATA'])/'RhinoSceneFlow/postproduction'
        hashes={p.parent.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (data/'boards').glob('*/board.json')}
        status=c.api('/status');prefs=c.api('/board-preferences');catalog=c.api('/boards')
        write('baseline.json',dict(native=native,preferences=prefs,boards=catalog,boardHashes=hashes,webVersion=status['version']))
        print(json.dumps(dict(native=native,webVersion=status['version'],boards=len(catalog)),ensure_ascii=False))
    elif command=='case':
        if (OUT/'case.json').exists():raise RuntimeError('Case already exists; do not duplicate blindly')
        c=client();base=json.loads((OUT/'baseline.json').read_text());boards=c.api('/boards');source=next((b for b in boards if 'Hillside' in b['name']),boards[0] if boards else None)
        assert source,'Need an existing case or exported PSD'
        b=c.api('/boards/'+source['id']+'/duplicate',dict(name='UX audit - Hillside - 2026-11-10'));n=next(n for n in b['nodes'] if n.get('original'))
        c.patch(b['id'],selectedId=n['id'],view={**b['view'],'mode':'list'});c.api('/board-preferences',dict(lastBoard=b['id'],language='en'),'PUT')
        write('case.json',dict(board=b['id'],sourceBoard=source['id'],sourceNode=n['id'],sourceAsset=n['asset']));print(json.dumps(dict(board=b['id'],nodes=len(b['nodes']))))
    elif command=='file':
        source=Path(sys.argv[2]).read_text(encoding='utf-8-sig');print(json.dumps(run(source),ensure_ascii=False))
    else:raise ValueError('startup | baseline | case | file SCRIPT')

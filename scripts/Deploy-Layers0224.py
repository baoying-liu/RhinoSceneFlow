"""Explicit B-only managed deployment, graceful Web shutdown, durable manager task."""
import importlib.machinery,json,sys,uuid,subprocess,urllib.request,time,os
from pathlib import Path
m=importlib.machinery.SourceFileLoader('audit',str(Path(__file__).with_name('Studio-Audit-Mcp.py'))).load_module();root=m.ROOT;out=root/'artifacts/rhino-B/layers0224';out.mkdir(parents=True,exist_ok=True)
def manager(name,args):
 p=out/'manager-request.json';m.write(p,args)
 return json.loads(subprocess.check_output([sys.executable,str(root/'scripts/Sandbox-Mcp.py'),name,str(p)]))
if sys.argv[1]=='start':
 c=m.StudioMcp(out)
 script="import Rhino,System,json\nd=Rhino.RhinoDoc.ActiveDoc\nassert System.Diagnostics.Process.GetCurrentProcess().Id=="+str(c.pid)+"\nprint('SF_DOC:'+json.dumps(dict(pid=System.Diagnostics.Process.GetCurrentProcess().Id,serial=int(d.RuntimeSerialNumber),objects=d.Objects.Count,modified=d.Modified,path=d.Path)))"
 req=urllib.request.Request('http://127.0.0.1:'+str(c.port)+'/',data=json.dumps(dict(jsonrpc='2.0',id=1,method='tools/call',params=dict(name='run_python',arguments=dict(script=script)))).encode(),headers={'Content-Type':'application/json','Accept':'application/json, text/event-stream'})
 result=json.load(urllib.request.urlopen(req,timeout=60));doc=None
 for item in result['result']['content']:
  for line in item.get('text','').splitlines():
   if line.startswith('SF_DOC:'):doc=json.loads(line[7:])
 assert doc; m.write(out/'before.json',doc)
 # Refuses if the user has started any active Web task; never terminate its process.
 # The original Platform bridge intentionally excludes shutdown; use its existing authenticated endpoint.
 service=m.load(Path(os.environ['LOCALAPPDATA'])/'RhinoSceneFlow/postproduction/service.json')
 req=urllib.request.Request('http://127.0.0.1:'+str(service['port'])+'/api/shutdown',data=b'{}',headers={'Authorization':'Bearer '+service['token'],'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=10) as response:assert json.load(response)['stopping']
 response=manager('start_job',dict(operation='build_test',requestId='office-20261109-layers0224-'+uuid.uuid4().hex));m.write(out/'job.json',response);print(json.dumps(response))
elif sys.argv[1]=='status':
 job=m.load(out/'job.json');id=job.get('jobId') or job.get('JobId') or job.get('Job',{}).get('JobId');assert id,job
 status=manager('job_status',dict(jobId=id,logLines=12));m.write(out/'status.json',status);print(json.dumps(status,ensure_ascii=False))
else:raise ValueError('start | status')

"""External B-only native New/Open regression. HTTP reset alone is never a crash/pass."""
import json,subprocess,sys,time
from pathlib import Path
root=Path(__file__).resolve().parents[1]
out=root/'artifacts/rhino-B/document-switch';out.mkdir(parents=True,exist_ok=True)
client=root/'scripts/Rhino-Mcp.py'
reports=[]
def run(source,label):
 path=out/(label+'.py');path.write_text(source,encoding='utf-8')
 p=subprocess.run([sys.executable,str(client),'run_python',str(path)],capture_output=True,text=True,encoding='utf-8',timeout=35)
 (out/(label+'-rpc.json')).write_text(p.stdout+'\n'+p.stderr,encoding='utf-8')
 assert p.returncode==0,(label,p.stderr)
 reply=json.loads(p.stdout);text=''.join(c.get('text','') for c in reply['result']['content'])
 assert 'Traceback' not in text,(label,text)
 return json.loads(text)
prefix="""import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,**kw))))
 assert r['ok'],r
 return r['result']
"""
def state(label,previous=None):
 return run(prefix+f"""
assert api('describe')['version']=='0.13.3'
s=api('material_workspace_status');serial=int(doc.RuntimeSerialNumber);previous={previous!r}
assert previous is None or serial!=previous,serial
assert all(t['document']==serial and t['error'] is None for t in s['tools'].values()),s
print(json.dumps(dict(pid=EXPECTED_PID,document=serial,tools=s['tools'])))
""",label)
initial=state('initial');pid=initial['pid'];serial=initial['document']
for i,action in enumerate(['new','open','new','open','new','open']):
 prep=run(prefix+"""
assert doc.Objects.Count==0 or doc.Path.lower().endswith('owned-open.3dm'),doc.Path
api('material_workspace_group')
if doc.NamedViews.Count==0:doc.NamedViews.Add('Lifecycle_Owned',doc.Views.ActiveView.ActiveViewport.Id)
api('material_workspace_open',page='export')
doc.Modified=False
print(json.dumps(dict(pid=EXPECTED_PID,document=int(doc.RuntimeSerialNumber))))
""",'prepare-'+str(i))
 assert prep['pid']==pid and prep['document']==serial
 # Exercise ready WebView disposal, not only construction.
 run(prefix+"api('material_workspace_open',page='materials');print(json.dumps(dict(open=True)))",'ai-'+str(i))
 time.sleep(2)
 command='_-New _None' if action=='new' else '_-Open "'+str(out/'owned-open.3dm')+'" _Enter'
 path=out/('command-'+str(i)+'.json');path.write_text(json.dumps(dict(command=command)),encoding='utf-8')
 p=subprocess.run([sys.executable,str(client),'run_command',str(path)],capture_output=True,text=True,encoding='utf-8',timeout=35)
 (out/('command-'+str(i)+'-rpc.log')).write_text(p.stdout+'\n'+p.stderr,encoding='utf-8')
 time.sleep(1)
 after=state('after-'+str(i),serial);assert after['pid']==pid
 reports.append(dict(action=action,before=serial,after=after['document'],samePid=True,allToolsRebound=True))
 serial=after['document']
 print(json.dumps(reports[-1]),flush=True)
with open(out/'verified.json','w',encoding='utf-8') as f:json.dump(dict(pid=pid,transitions=reports),f,indent=2)

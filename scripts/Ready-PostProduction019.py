import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
folder=os.path.join(OUTPUT_DIR,'postproduction019');record=json.load(open(os.path.join(folder,'before.json')))
doc=__rhino_doc__;assert doc.Objects.Count==0 and not doc.Modified and doc.Path is None
assert int(doc.RuntimeSerialNumber)!=json.load(open(os.path.join(folder,'new-before.json')))['previousSerial']
r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation='material_workspace_status'))));assert r['ok'] and all(t['error'] is None for t in r['result']['tools'].values()),r
json.dump(dict(pid=EXPECTED_PID,newPassed=True,allToolsHealthy=True),open(os.path.join(folder,'new.json'),'w'))
assert not record['modified'],'Dirty recovery must use the sandbox backup, never discard user work'
assert os.path.isfile(record['path'])
assert Rhino.RhinoApp.RunScript('_-Open "'+record['path']+'" _Enter',False)
print('Restored the saved pre-update B model')

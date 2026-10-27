import System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'xatlas');s=json.load(open(os.path.join(folder,'guard-cancel.json')))
r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation='material_unwrap_status',jobId=s['cancel']['id']))));assert r['ok'],r;assert r['result']['status']=='cancelled',r
o=doc.Objects.FindId(System.Guid(s['object']));assert o.Attributes.GetUserString('RhinoSceneFlow.WorldUv') is None
doc.Objects.Delete(o.Id,True);s.update(cancelResult=r['result'],passed=True)
with open(os.path.join(folder,'guards-verified.json'),'w') as f:json.dump(s,f,indent=2)
print('PASS: source edit rejects stale commit; cancellation leaves no UV changes')

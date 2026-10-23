"""Actual B-only 8192x2048 workbench export, beyond the legacy pixel cap."""
import clr,Rhino,System,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
original=api('workbench_settings')['views'][0]
before=(doc.Modified,str(doc.Views.ActiveView.ActiveViewport.CameraLocation),str(doc.Views.ActiveView.ActiveViewport.Size))
try:
 api('configure_view',viewId=original['id'],settings=dict(width=8192,height=2048,layers=[dict(kind='material')]))
 out=os.path.join(OUTPUT_DIR,'workbench','8k-'+str(System.Guid.NewGuid())[:8])
 result=api('export_workbench',directory=out,views=[original['id']]);assert all(f['ok'] for f in result['files']),result
 assert before==(doc.Modified,str(doc.Views.ActiveView.ActiveViewport.CameraLocation),str(doc.Views.ActiveView.ActiveViewport.Size))
 with open(os.path.join(OUTPUT_DIR,'workbench','8k-report.json'),'w') as f:json.dump(dict(ok=True,pid=EXPECTED_PID,result=result,stateUnchanged=True),f,indent=2)
 print(json.dumps(result))
finally:api('configure_view',viewId=original['id'],settings=original)

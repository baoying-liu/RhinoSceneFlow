"""Verify existing layered PSD export against the material demo, preserving config."""
import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
settings=api('workbench_settings');original=next(v for v in settings['views'] if v['name']=='Materials_Perspective')
mode=next(m['id'] for m in settings['displayModes'] if m['name']=='Rendered')
v=doc.Views.ActiveView.ActiveViewport;before=(doc.Modified,str(v.CameraLocation),str(v.CameraDirection),str(v.Size),int(doc.RenderSettings.Sun.Hash))
try:
 api('configure_view',viewId=original['id'],settings=dict(width=320,height=200,layers=[dict(kind='display',mode=mode),dict(kind='shadow'),dict(kind='material')]))
 directory=os.path.join(OUTPUT_DIR,'materials','demo','export-'+str(System.Guid.NewGuid())[:8])
 result=api('export_workbench',directory=directory,views=[original['id']]);assert all(f['ok'] for f in result['files']),result
 assert before==(doc.Modified,str(v.CameraLocation),str(v.CameraDirection),str(v.Size),int(doc.RenderSettings.Sun.Hash))
 with open(os.path.join(OUTPUT_DIR,'materials','demo','export-report.json'),'w') as f:json.dump(dict(ok=True,pid=EXPECTED_PID,result=result,stateUnchanged=True),f,indent=2)
 print(json.dumps(result))
finally:api('configure_view',viewId=original['id'],settings=original)

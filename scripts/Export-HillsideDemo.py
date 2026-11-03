"""One actual layered PSD, with the panel's 1600x1200 preset restored afterwards."""
import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi,WorkbenchService
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.abspath(os.path.join(OUTPUT_DIR,'..','examples','Hillside-Retreat'))
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
views=api('named_views');view=next(v for v in views if v['name']=='01 Hillside Axon');before=doc.Modified
api('configure_view',viewId=view['id'],settings=dict(width=1200,height=900))
try:
 report=api('export_workbench',directory=os.path.join(folder,'PSD'),views=[view['id']],collision='number')
 assert len(report['files'])==1 and all(f['ok'] for f in report['files']),report
 assert doc.Modified==before,'Export changed document modified state'
 with open(os.path.join(folder,'export.json'),'w') as f:json.dump(report,f,indent=2)
finally:api('configure_view',viewId=view['id'],settings=dict(width=1600,height=1200))
print(json.dumps(report))

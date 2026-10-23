"""B-only final build: synthetic Eto wheel events, all previews and small export."""
import clr,Rhino,System,json,os
from System.Reflection import BindingFlags
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import ExportPanelController,McpApi
from Eto.Forms import MouseEventArgs,MouseButtons,Keys
from Eto.Drawing import PointF,SizeF
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;p=ExportPanelController.Open(doc)
def field(obj,name):return obj.GetType().GetField(name,BindingFlags.Instance|BindingFlags.NonPublic).GetValue(obj)
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
before=(doc.Modified,str(doc.Views.ActiveView.ActiveViewport.CameraLocation),str(doc.Views.ActiveView.ActiveViewport.Size),int(doc.RenderSettings.Sun.Hash),tuple((str(v.MainViewport.Id),v.Floating) for v in doc.Views.GetViewList(True,True)))
original=p.Views[0].Copy()
try:
 p.OpenDetails(original.Id);detail=field(p,'detail');image=field(detail,'image');method=image.GetType().GetMethod('OnMouseWheel',BindingFlags.Instance|BindingFlags.NonPublic)
 start=p.Views[0].Camera.Zoom
 for delta,expected in [(120,start*1.1),(-120,start)]:
  event=MouseEventArgs(System.Enum.ToObject(MouseButtons,0),System.Enum.ToObject(Keys,0),PointF(0,0),SizeF(0,delta),System.Single(1))
  method.Invoke(image,System.Array[System.Object]([event]));assert abs(p.Views[0].Camera.Zoom-expected)<1e-10
 p.CloseDetails()
 api('configure_view',viewId=str(original.Id),settings=dict(width=256,height=160,layers=[dict(kind='shadow'),dict(kind='material')]))
 out=os.path.join(OUTPUT_DIR,'workbench','final-'+str(System.Guid.NewGuid())[:8]);files=api('export_workbench',directory=out,views=[str(original.Id)])
 assert all(f['ok'] for f in files['files']),files
finally:p.SetView(original)
for row in p.Views:p.RefreshCard(row.Id)
state=api('panel_status');assert all(v['loaded'] for v in state['previews'])
assert before==(doc.Modified,str(doc.Views.ActiveView.ActiveViewport.CameraLocation),str(doc.Views.ActiveView.ActiveViewport.Size),int(doc.RenderSettings.Sun.Hash),tuple((str(v.MainViewport.Id),v.Floating) for v in doc.Views.GetViewList(True,True)))
result=dict(ok=True,pid=EXPECTED_PID,version=api('describe')['version'],wheel120Normalized=True,previews=len(state['previews']),floatingViews=sum(1 for v in doc.Views.GetViewList(True,True) if v.Floating),files=files,stateUnchanged=True)
with open(os.path.join(OUTPUT_DIR,'workbench','final-verified.json'),'w') as f:json.dump(result,f,indent=2)
print(json.dumps(result))

"""Poll after Test-WorkbenchAsync.py and restore settings when complete."""
import clr,Rhino,System,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import ExportPanelController,SceneFlowPlugin,McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
app=System.AppDomain.CurrentDomain;task=app.GetData('WorkbenchTask');assert task is not None
done=task.IsCompleted;print(json.dumps(dict(completed=done)))
if done:
 app.GetData('WorkbenchTimer').Stop();doc=__rhino_doc__;p=ExportPanelController.Find(doc.RuntimeSerialNumber)
 state=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation='panel_status',document=int(doc.RuntimeSerialNumber)))))['result']
 cancel=bool(app.GetData('WorkbenchTestCancel'));out=str(app.GetData('WorkbenchOut'))
 try:
  assert not task.IsFaulted and not p.IsExporting
  assert state['lastReport']['cancelled']==cancel,state
  if cancel:assert not os.path.exists(out) or not os.listdir(out),os.listdir(out)
  else:assert len(state['lastReport']['files'])==2 and all(f['ok'] for f in state['lastReport']['files']),state
  ticks=int(app.GetData('WorkbenchTicks'));assert ticks>0
  before=json.loads(str(app.GetData('WorkbenchBefore')))
  assert before==[doc.Modified,str(doc.Views.ActiveView.ActiveViewport.CameraLocation),str(doc.Views.ActiveView.ActiveViewport.Size),int(doc.RenderSettings.Sun.Hash),len(list(doc.Views.GetViewList(False,True)))]
  result=dict(ok=True,cancel=cancel,uiBusyTicks=ticks,report=state['lastReport'],stateUnchanged=True)
  with open(os.path.join(OUTPUT_DIR,'workbench','cancel-verified.json' if cancel else 'async-verified.json'),'w') as f:json.dump(result,f,indent=2)
  print(json.dumps(result))
 finally:
  for r in app.GetData('WorkbenchSavedRows'):p.SetView(r)
  SceneFlowPlugin.Instance.ExportDirectory=str(app.GetData('WorkbenchSavedDirectory'))
  app.SetData('WorkbenchTestCancel',False)

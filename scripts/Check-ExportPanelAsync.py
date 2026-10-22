"""Poll after Test-ExportPanelAsync.py; keep the Rhino UI dispatcher free."""
import clr,Rhino,System,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi,SceneFlowPlugin
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
app=System.AppDomain.CurrentDomain;task=app.GetData('SceneFlowUiTask');assert task is not None
print(json.dumps(dict(completed=task.IsCompleted,ticks=int(app.GetData('SceneFlowUiTicks')))))
if task.IsCompleted:
    app.GetData('SceneFlowUiTimer').Stop()
    state=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation='panel_status',document=int(__rhino_doc__.RuntimeSerialNumber)))))['result']
    assert not state['busy'] and state['lastReport'] and all(f['ok'] for f in state['lastReport']['files']),state
    busy_ticks=int(app.GetData('SceneFlowUiBusyTicks'));assert busy_ticks>0,'UI timer did not run during the export'
    before=json.loads(str(app.GetData('SceneFlowUiBefore')));doc=__rhino_doc__
    assert before==[doc.Modified,str(doc.Views.ActiveView.ActiveViewport.CameraLocation),str(doc.Views.ActiveView.ActiveViewport.Size)]
    SceneFlowPlugin.Instance.ExportDirectory=str(app.GetData('SceneFlowPreviousDirectory'))
    with open(os.path.join(OUTPUT_DIR,'panel','async-report.json'),'w',encoding='utf-8') as f:
        json.dump(dict(ok=True,uiBusyTicks=busy_ticks,state=state),f,indent=2)
    print(json.dumps(state['lastReport']))

import clr,Rhino,System,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi,SceneFlowPlugin
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
app=System.AppDomain.CurrentDomain;task=app.GetData('SceneFlowCancelTask');assert task is not None
print(json.dumps(dict(completed=task.IsCompleted)))
if task.IsCompleted:
    app.GetData('SceneFlowCancelTimer').Stop()
    state=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation='panel_status',document=int(__rhino_doc__.RuntimeSerialNumber)))))['result']
    assert not state['busy'] and state['lastReport']['cancelled'],state
    out=str(app.GetData('SceneFlowCancelDirectory'))
    assert not os.path.isdir(out) or not os.listdir(out),'Cancellation left an output or temporary file'
    SceneFlowPlugin.Instance.ExportDirectory=str(app.GetData('SceneFlowPreviousDirectory'))
    result=dict(ok=True,via=str(app.GetData('SceneFlowCancelVia')),state=state,emptyOutput=True)
    with open(os.path.join(OUTPUT_DIR,'panel','cancel-report.json'),'w',encoding='utf-8') as f:json.dump(result,f,indent=2)
    print(json.dumps(dict(cancelled=True,via=result['via'],emptyOutput=True)))

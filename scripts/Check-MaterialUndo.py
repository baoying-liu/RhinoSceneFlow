import Rhino,System,json,os
D=__rhino_doc__;app=System.AppDomain.CurrentDomain;id=System.Guid(str(app.GetData('SceneFlowUndoFixture')));obj=D.Objects.FindId(id)
result=dict(pid=EXPECTED_PID,undo=bool(app.GetData('SceneFlowUndoResult')),fixtureExists=obj is not None,bindingRemoved=obj is not None and obj.Attributes.GetUserString('RhinoSceneFlow.Material') is None)
try:
 assert result['undo'] and result['fixtureExists'] and result['bindingRemoved'],result
 with open(os.path.join(OUTPUT_DIR,'materials','demo','undo-verified.json'),'w') as f:json.dump(result,f,indent=2)
 print(json.dumps(result))
finally:
 if obj is not None and obj.Attributes.GetUserString('SceneFlow.UndoTest')=='v0.7':D.Objects.Delete(id,True)
 app.GetData('SceneFlowUndoTimer').Dispose()

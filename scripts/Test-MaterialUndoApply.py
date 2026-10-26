import Rhino,System,json,clr
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
D=__rhino_doc__;app=System.AppDomain.CurrentDomain
r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation='material_apply',document=int(D.RuntimeSerialNumber),assetId=str(app.GetData('SceneFlowUndoAsset')),objects=[str(app.GetData('SceneFlowUndoFixture'))],mapping=dict(mode='plane')))));assert r['ok'],r
print(json.dumps(dict(applied=True,undoActive=D.UndoRecordingIsActive)))

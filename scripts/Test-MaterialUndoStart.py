import Rhino,System,json,clr,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
D=__rhino_doc__;demo=json.load(open(os.path.join(OUTPUT_DIR,'materials','demo','ready.json')))
g=Rhino.Geometry.Brep.CreateFromCornerPoints(Rhino.Geometry.Point3d(20000,0,0),Rhino.Geometry.Point3d(21000,0,0),Rhino.Geometry.Point3d(21000,1000,0),Rhino.Geometry.Point3d(20000,1000,0),.001)
a=Rhino.DocObjects.ObjectAttributes();a.SetUserString('SceneFlow.UndoTest','v0.7');id=D.Objects.AddBrep(g,a)
System.AppDomain.CurrentDomain.SetData('SceneFlowUndoFixture',str(id));System.AppDomain.CurrentDomain.SetData('SceneFlowUndoAsset',demo['ai']['id'])
print(json.dumps(dict(id=str(id),undoActive=D.UndoRecordingIsActive)))

import Rhino,System,json,os,clr
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import MaterialQuickController
D=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'materials-v09');s=json.load(open(os.path.join(folder,'selection-state.json')));assert s['pid']==EXPECTED_PID
p=MaterialQuickController.Find(D.RuntimeSerialNumber)
try:
 assert not p.Busy
 for i in [0,1]:
  o=D.Objects.FindId(System.Guid(s['ids'][i]));assert o.Attributes.GetUserString('RhinoSceneFlow.Material') is not None and o.Attributes.MaterialSource==Rhino.DocObjects.ObjectMaterialSource.MaterialFromLayer
 assert D.Objects.FindId(System.Guid(s['ids'][3])).Attributes.GetUserString('RhinoSceneFlow.Material') is None
 assert D.Objects.FindId(System.Guid(s['ids'][2])).Attributes.MaterialSource==Rhino.DocObjects.ObjectMaterialSource.MaterialFromObject
 s['currentLayerAndClickSnapshot']=True;s['complete']=True
 with open(os.path.join(folder,'selection-verified.json'),'w') as f:json.dump(s,f,indent=2)
 print(json.dumps(dict(selectionRegressionPassed=True)))
finally:
 if p is not None:p.Close()
 for id in s['ids']:
  o=D.Objects.FindId(System.Guid(id))
  if o is not None and o.Attributes.GetUserString('SceneFlow.LiveSelectionTest')==s['stamp']:D.Objects.Delete(o.Id,True)
 for id in s['layers']:
  l=D.Layers.FindId(System.Guid(id))
  if l is not None and not list(D.Objects.FindByLayer(l)):D.Layers.Delete(l.Index,True)
 D.Objects.UnselectAll()
 for id in s['selection']:
  o=D.Objects.FindId(System.Guid(id))
  if o is not None:o.Select(True)
 D.Modified=s['modified'];D.Views.Redraw()

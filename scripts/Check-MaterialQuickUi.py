import Rhino,System,json,os,clr
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import MaterialQuickController,McpApi
D=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'worlduv');state=json.load(open(os.path.join(folder,'quick-ui-state.json')))
assert state['pid']==EXPECTED_PID
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(D.RuntimeSerialNumber),**kw))));assert r['ok'],r
 return r['result']
try:
 result=api('material_quick_status');assert not result['busy'] and result['progress']==100,result
 assert any('1/2' in s for s in result['history']) and any('2/2' in s for s in result['history']),result
 for id in state['ids']:
  o=D.Objects.FindId(System.Guid(id));assert o.Attributes.MaterialSource==Rhino.DocObjects.ObjectMaterialSource.MaterialFromLayer
  assert api('material_uv_status',objects=[id])[0]['status']['valid']
 result['passed']=True
 with open(os.path.join(folder,'quick-ui-verified.json'),'w') as f:json.dump(result,f,indent=2)
 print(json.dumps(result))
finally:
 p=MaterialQuickController.Find(D.RuntimeSerialNumber)
 if p is not None:p.Close()
 for id in state['ids']:
  o=D.Objects.FindId(System.Guid(id))
  if o is not None and o.Attributes.GetUserString('SceneFlow.QuickUiTest')=='v0.8':D.Objects.Delete(o.Id,True)
 layer=D.Layers.FindId(System.Guid(state['layer']))
 if layer is not None:D.Layers.Delete(layer.Index,True)
 D.Objects.UnselectAll()
 for id in state['selection']:
  o=D.Objects.FindId(System.Guid(id))
  if o is not None:o.Select(True)
 D.Modified=state['modified'];D.Views.Redraw()

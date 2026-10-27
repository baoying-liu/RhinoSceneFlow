"""Start A -> B selection regression in the real Eto panel. Continue with Check-LiveMaterialSelection.py."""
import Rhino,System,json,os,clr
from System.Reflection import BindingFlags
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi,MaterialQuickController
D=__rhino_doc__;assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
stamp=str(System.Guid.NewGuid())[:8];folder=os.path.join(OUTPUT_DIR,'materials-v09');os.makedirs(folder,exist_ok=True)
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(D.RuntimeSerialNumber),**kw))));assert r['ok'],r
 return r['result']
assets=api('material_library')['assets'];assert assets
state=dict(pid=EXPECTED_PID,stamp=stamp,selection=[str(o.Id) for o in D.Objects.GetSelectedObjects(False,False)],modified=D.Modified,ids=[],layers=[],asset=assets[0]['id'])
for name,x in [('A',22000),('B',25000)]:
 layer=Rhino.DocObjects.Layer();layer.Name='SceneFlow_LiveSelection_'+name+'_'+stamp;index=D.Layers.Add(layer);state['layers'].append(str(D.Layers[index].Id))
 for n in range(2):
  a=Rhino.DocObjects.ObjectAttributes();a.Name=name+str(n);a.LayerIndex=index;a.SetUserString('SceneFlow.LiveSelectionTest',stamp)
  g=Rhino.Geometry.Brep.CreateFromCornerPoints(Rhino.Geometry.Point3d(x,n*1500,0),Rhino.Geometry.Point3d(x+1000,n*1500,0),Rhino.Geometry.Point3d(x+1000,n*1500+1000,0),Rhino.Geometry.Point3d(x,n*1500+1000,0),.001)
  state['ids'].append(str(D.Objects.AddBrep(g,a)));g.Dispose()
p=MaterialQuickController.Open(D,System.Array[System.Guid]([System.Guid(state['ids'][0])]))
p.SelectAsset(System.Guid(state['asset']))
# Deselect A, select B while the same panel remains open; apply must use B.
D.Objects.UnselectAll();D.Objects.FindId(System.Guid(state['ids'][2])).Select(True)
p.GetType().GetMethod('Start',BindingFlags.Instance|BindingFlags.NonPublic).Invoke(p,System.Array[System.Object]([False]));assert p.Busy
# A selection made after clicking must not redirect the already-running B operation.
D.Objects.UnselectAll();D.Objects.FindId(System.Guid(state['ids'][0])).Select(True)
with open(os.path.join(folder,'selection-state.json'),'w') as f:json.dump(state,f,indent=2)
print(json.dumps(api('material_quick_status')))

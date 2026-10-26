"""Begin real Eto application workflow; run Check-MaterialQuickUi.py after UI ticks."""
import Rhino,System,json,os,clr
from System.Reflection import BindingFlags
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import MaterialQuickController,McpApi
D=__rhino_doc__;assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(D.RuntimeSerialNumber),**kw))));assert r['ok'],r
 return r['result']
ready=json.load(open(os.path.join(OUTPUT_DIR,'materials','demo','ready.json')))
layer=Rhino.DocObjects.Layer();layer.Name='SceneFlow_QuickUi_'+str(System.Guid.NewGuid())[:8];index=D.Layers.Add(layer)
state=dict(selection=[str(o.Id) for o in D.Objects.GetSelectedObjects(False,False)],modified=D.Modified,layer=str(D.Layers[index].Id),ids=[])
for x in [0,2000]:
 a=Rhino.DocObjects.ObjectAttributes();a.LayerIndex=index;a.SetUserString('SceneFlow.QuickUiTest','v0.8')
 g=Rhino.Geometry.Brep.CreateFromCornerPoints(Rhino.Geometry.Point3d(x,0,0),Rhino.Geometry.Point3d(x+1000,0,0),Rhino.Geometry.Point3d(x+1000,1000,0),Rhino.Geometry.Point3d(x,1000,0),.001)
 state['ids'].append(str(D.Objects.AddBrep(g,a)));g.Dispose()
api('material_prepare_uv',objects=[state['ids'][0]])
p=MaterialQuickController.Open(D,System.Array[System.Guid]([System.Guid(i) for i in state['ids']]))
p.SelectAsset(System.Guid(ready['calibration']['id']))
flags=BindingFlags.Instance|BindingFlags.NonPublic
p.GetType().GetField('scope',flags).GetValue(p).SelectedKey='layer'
p.GetType().GetMethod('Start',flags).Invoke(p,System.Array[System.Object]([False]))
assert p.Busy,'Not busy'
state['pid']=EXPECTED_PID
folder=os.path.join(OUTPUT_DIR,'worlduv');os.makedirs(folder,exist_ok=True)
with open(os.path.join(folder,'quick-ui-state.json'),'w') as f:json.dump(state,f)
print(json.dumps(api('material_quick_status')))

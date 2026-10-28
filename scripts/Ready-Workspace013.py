"""Final installed-build smoke on the saved owned model, plus no-match semantic search (no image request)."""
import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin');clr.AddReference('RhinoSceneFlow.Core')
from RhinoSceneFlow.Plugin import McpApi,ExportPanelController,ExportLayerSetting
from RhinoSceneFlow.Core import CodexCatalogRunner,MaterialLibrary
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'workspace013');fixture=json.load(open(os.path.join(folder,'setup.json')))
assert doc.Path and doc.Path.endswith('SceneFlow-Workspace013.3dm'),doc.Path
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
assert api('describe')['version']=='0.13.0';api('material_workspace_group')
generated=json.load(open(os.path.join(folder,'generation-verified.json')))['asset']['id'];api('material_tool_select',assetId=generated)
state=api('material_quick_status');assert state['selected']==generated and state['shelf']['selected']==generated,state
assert state['reuseSimilar'] is True
uv=api('material_uv_status',objects=fixture['objects']);assert all(v['status']['valid'] for v in uv),uv
wrong=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation='material_tool_apply',document=4294967295))));assert not wrong['ok']
api('material_workspace_open',page='export');p=ExportPanelController.Find(doc.RuntimeSerialNumber);r=p.Views[0].Copy();r.Width=320;r.Height=240
shadow=ExportLayerSetting();shadow.Kind='shadow';shadow.Blend='mul ';shadow.Opacity=75
texture=ExportLayerSetting();texture.Kind='texture'
arctic=ExportLayerSetting();arctic.Kind='display';arctic.Mode=System.Guid(next(m['id'] for m in api('workbench_settings')['displayModes'] if m['name']=='Arctic'))
r.Layers.Clear();r.Layers.Add(shadow);r.Layers.Add(texture);r.Layers.Add(arctic);p.SetView(r);p.RefreshCard(r.Id)
api('material_workspace_open',page='materials');api('material_shelf_open',visible=True)
assets=MaterialLibrary(api('material_library')['directory']).List()
task=CodexCatalogRunner.RunAsync(os.path.join(folder,'no-match'),'search','生成鲜红色抛光铜金属，明显金属反光，不要石头或陶瓷。',assets,System.Threading.CancellationToken(False))
System.AppDomain.CurrentDomain.SetData('Workspace013NoMatch',task)
report=dict(pid=EXPECTED_PID,document=int(doc.RuntimeSerialNumber),model=doc.Path,workspace=api('material_workspace_status'),uvValid=True,selectedAssetSynced=True,wrongDocumentRejected=True,noMatchTaskStarted=True)
with open(os.path.join(folder,'ready.json'),'w') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(pid=EXPECTED_PID,model=doc.Path,uvValid=True,selectedAssetSynced=True,wrongDocumentRejected=True)))

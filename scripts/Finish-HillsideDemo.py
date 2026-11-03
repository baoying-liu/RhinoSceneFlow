"""Verify current model bindings and save previews/model using shipped SceneFlow services."""
import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi,WorkbenchService,ExportPanelController
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.abspath(os.path.join(OUTPUT_DIR,'..','examples','Hillside-Retreat'))
data=json.load(open(os.path.join(folder,'geometry.json')));applied=json.load(open(os.path.join(folder,'applied.json')));planting=json.load(open(os.path.join(folder,'planting.json')))
assert set(applied)=={'grass','cedar','roof'},applied
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
state=api('plant_group_state',groupId=planting['group']);assert not state['busy'] and state['error'] is None and state['count']>0,state
ids=[oid for group in data['materialsets'].values() for oid in group]
uv=api('material_uv_status',objects=ids)
assert len(uv)==len(ids) and all(row['status']['valid'] and row['status']['metersPerUv']==1 for row in uv),uv
display=os.path.join(folder,'display.json');rendered=json.load(open(display))['mode'] if os.path.exists(display) else str(Rhino.Display.DisplayModeDescription.RenderedId);arctic=str(next(m.Id for m in Rhino.Display.DisplayModeDescription.GetDisplayModes() if m.EnglishName=='Arctic'))
views=api('named_views')
for view in views:
 api('configure_view',viewId=view['id'],settings=dict(width=1600,height=1200,mode=rendered,layers=[dict(kind='plants',plantGrouping='species'),dict(kind='shadow',blend='mul ',opacity=45),dict(kind='texture',textureGrouping='material'),dict(kind='display',mode=arctic)],plantShadows=True))
for row in WorkbenchService.Settings(doc):
 b=WorkbenchService.Preview(doc,row,1200);b.Save(os.path.join(folder,row.Name+'.png'),System.Drawing.Imaging.ImageFormat.Png);b.Dispose()
doc.NamedViews.Restore(0,doc.Views.ActiveView,False);doc.Views.ActiveView.ActiveViewport.DisplayMode=Rhino.Display.DisplayModeDescription.GetDisplayMode(System.Guid(rendered));doc.Objects.UnselectAll();doc.Views.Redraw()
model=json.load(open(os.path.join(folder,'views.json')))['model'];assert doc.Path==model
assert Rhino.RhinoApp.RunScript('_-Save _Enter',False);assert not doc.Modified
api('plant_select',assetId=planting['asset']['id']);doc.Objects.Select(System.Guid(planting['group']));doc.Views.Redraw()
health=api('material_workspace_status');assert all(t['error'] is None for t in health['tools'].values())
# Native selection only; save was already completed, no modal save/export dialogs.
receipt=dict(pid=EXPECTED_PID,model=model,views=views,objects=len(ids),trees=state['count'],manual=state['manual'],plantingGroup=planting['group'],carrier=data['carrier'],library=api('material_library')['directory'],uv=uv,assets=applied,allToolsHealthy=True,modified=doc.Modified)
with open(os.path.join(folder,'ready.json'),'w') as f:json.dump(receipt,f,indent=2)
print(json.dumps(dict(model=model,objects=len(ids),trees=state['count'],manual=state['manual'],views=len(views),modified=doc.Modified)))

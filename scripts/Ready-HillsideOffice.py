"""Post-native-Open validation and final user-facing Plants List selection."""
import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi,WorkbenchService
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.abspath(os.path.join(OUTPUT_DIR,'..','examples','Hillside-Retreat'));ready=json.load(open(os.path.join(folder,'ready.json')));before=json.load(open(os.path.join(folder,'reopen-before.json')))
assert EXPECTED_PID==before['pid'] and int(doc.RuntimeSerialNumber)!=before['document'] and doc.Path==ready['model'] and not doc.Modified
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
data=json.load(open(os.path.join(folder,'geometry.json')));ids=list(data['objects'].values());uv=api('material_uv_status',objects=ids)
assert len(uv)==69 and all(r['status']['valid'] and r['status']['metersPerUv']==1 for r in uv),uv
state=api('plant_group_state',groupId=ready['plantingGroup']);assert not state['busy'] and not state['error'] and state['count']==15 and state['manual']==4,state
assert len(api('named_views'))==3
for page in ['materials','library','uv','planting','export','properties','plantsList']:api('material_workspace_open',page=page)
health=api('material_workspace_status');assert len(health['pages'])==7 and all(t['error'] is None for t in health['tools'].values()),health
doc.NamedViews.Restore(0,doc.Views.ActiveView,False);doc.Views.ActiveView.Maximized=True
mode=Rhino.Display.DisplayModeDescription.GetDisplayMode(System.Guid(json.load(open(os.path.join(folder,'display.json')))['mode']));doc.Views.ActiveView.ActiveViewport.DisplayMode=mode
doc.Objects.UnselectAll();doc.Views.Redraw()
row=WorkbenchService.Settings(doc)[0];bitmap=WorkbenchService.Preview(doc,row,1200);bitmap.Save(os.path.join(folder,'Office-final-preview.png'),System.Drawing.Imaging.ImageFormat.Png);bitmap.Dispose()
api('plant_list_select',groups=[ready['plantingGroup']]);api('material_workspace_open',page='plantsList');doc.Views.Redraw()
assert not doc.Modified
report=dict(pid=EXPECTED_PID,document=int(doc.RuntimeSerialNumber),model=doc.Path,version=api('describe')['version'],objects=len(ids),uvValid=len(uv),trees=state['count'],manual=state['manual'],allToolsHealthy=True,modified=doc.Modified,library=api('material_library')['directory'],group=ready['plantingGroup'],views=api('named_views'))
with open(os.path.join(folder,'office-reopened.json'),'w') as f:json.dump(report,f,indent=2)
print(json.dumps(report))

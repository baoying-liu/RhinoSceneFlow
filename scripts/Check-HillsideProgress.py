import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi,WorkbenchService
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.abspath(os.path.join(OUTPUT_DIR,'..','examples','Hillside-Retreat'));planting=json.load(open(os.path.join(folder,'planting.json')))
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
state=api('plant_group_state',groupId=planting['group']);assert state['error'] is None,state
api('material_workspace_open',page='plantsList');api('plant_list_select',groups=[planting['group']])
doc.Objects.UnselectAll();doc.NamedViews.Restore(0,doc.Views.ActiveView,False)
mode=Rhino.Display.DisplayModeDescription.GetDisplayMode(System.Guid(json.load(open(os.path.join(folder,'display.json')))['mode']));doc.Views.ActiveView.ActiveViewport.DisplayMode=mode;doc.Views.Redraw()
b=WorkbenchService.Preview(doc,WorkbenchService.Settings(doc)[0],1200);b.Save(os.path.join(folder,'planting-preview.png'),System.Drawing.Imaging.ImageFormat.Png);b.Dispose()
assert doc.Path==json.load(open(os.path.join(folder,'views.json')))['model'];assert Rhino.RhinoApp.RunScript('_-Save _Enter',False);assert not doc.Modified
with open(os.path.join(folder,'progress-state.json'),'w') as f:json.dump(dict(count=state['count'],manual=state['manual'],busy=state['busy'],modelSaved=True),f,indent=2)
print(json.dumps(dict(count=state['count'],manual=state['manual'],busy=state['busy'])))

"""External-process updates must appear without overwriting local drafts; reject stale save."""
import Rhino,System,clr,json,os
from System.Reflection import BindingFlags
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
folder=os.path.join(OUTPUT_DIR,'shared-library0133');setup=json.load(open(os.path.join(folder,'setup.json')))
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,**kw))))
 assert r['ok'],r
 return r['result']
s=api('material_workspace_status');lib=s['tools']['library']['details'];assert lib['shelf']['count']==17,lib
panel=Rhino.UI.Panels.GetPanel(System.Guid(s['pages'][1]['panelId']))
tool=panel.GetType().GetProperty('Tool',BindingFlags.Instance|BindingFlags.NonPublic).GetValue(panel)
field=lambda o,n:o.GetType().GetField(n,BindingFlags.Instance|BindingFlags.NonPublic).GetValue(o)
shelf=field(tool,'shelf');assert field(shelf,'name').Text=='Unsaved local draft'
def buttons(control):
 from Eto.Forms import Button,Container
 if isinstance(control,Button):yield control
 if isinstance(control,Container):
  for child in control.Controls:
   for button in buttons(child):yield button
button=next(b for b in buttons(shelf) if b.Text=='保存属性');button.PerformClick()
assert '重新选择' in field(shelf,'status').Text,field(shelf,'status').Text
r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation='material_update',asset=setup['asset']))));assert not r['ok'],r
assets=api('material_library')['assets'];a=next(a for a in assets if a['id']==setup['asset']['id'])
assert a['revision']==41 and a['catalogRevision']==81 and abs(a['widthMeters']-1.04)<1e-8,a
assert a['name']!='Unsaved local draft'
# Re-selecting reads the current revision, and permits a deliberate new edit.
api('material_tool_select',page='library',assetId=a['id']);field(shelf,'name').Text='Shared checked in Rhino';button.PerformClick()
assert '已更新' in field(shelf,'status').Text,field(shelf,'status').Text
current=api('material_library')['assets'];edited=next(a for a in current if a['id']==setup['asset']['id']);assert edited['name']=='Shared checked in Rhino'
# Shared catalog is independent from Rhino document; in-process UI targets remain per-document.
chatData=[]
aiPanel=Rhino.UI.Panels.GetPanel(System.Guid(s['pages'][0]['panelId']));ai=aiPanel.GetType().GetProperty('Tool',BindingFlags.Instance|BindingFlags.NonPublic).GetValue(aiPanel)
host=field(field(ai,'chat'),'host');data=field(host,'data');assert 'sessions' in data and str(EXPECTED_PID) in data,data
report=dict(pid=EXPECTED_PID,automaticRefresh=True,localDraftPreserved=True,staleUiRejected=True,staleApiRejected=True,newSelectionCanSave=True,assetCount=len(current),chatData=data)
with open(os.path.join(folder,'verified.json'),'w') as f:json.dump(report,f,indent=2)
print(json.dumps(report))

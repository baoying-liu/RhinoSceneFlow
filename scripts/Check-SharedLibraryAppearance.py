"""A stale advanced editor must not undo another process's catalog organization."""
import Rhino,System,clr,json,os
from System.Reflection import BindingFlags
from Eto.Forms import Button,Container
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
folder=os.path.join(OUTPUT_DIR,'shared-library0133');setup=json.load(open(os.path.join(folder,'setup.json')))
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,**kw))))
 assert r['ok'],r
 return r['result']
s=api('material_workspace_status');panel=Rhino.UI.Panels.GetPanel(System.Guid(s['pages'][1]['panelId']))
tool=panel.GetType().GetProperty('Tool',BindingFlags.Instance|BindingFlags.NonPublic).GetValue(panel)
field=lambda o,n:o.GetType().GetField(n,BindingFlags.Instance|BindingFlags.NonPublic).GetValue(o)
def buttons(c):
 if isinstance(c,Button):yield c
 if isinstance(c,Container):
  for child in c.Controls:
   for button in buttons(child):yield button
field(tool,'width').Value=1600
next(b for b in buttons(tool) if b.Text=='保存尺寸与外观参数').PerformClick()
assert '重新选择' in field(tool,'status').Text,field(tool,'status').Text
asset=next(a for a in api('material_library')['assets'] if a['id']==setup['asset']['id'])
assert asset['category']=='Epoch-11' and abs(asset['widthMeters']-1.04)<1e-8,asset
report=json.load(open(os.path.join(folder,'verified.json')));report['staleAppearanceEditorRejected']=True;report['organizedCategoryPreserved']=True
with open(os.path.join(folder,'verified.json'),'w') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(pid=EXPECTED_PID,staleAppearanceEditorRejected=True,organizedCategoryPreserved=True)))

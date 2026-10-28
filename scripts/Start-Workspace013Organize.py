"""Real organize button, with immutable-image/appearance/binding snapshot."""
import Rhino,System,clr,json,os
from System.Reflection import BindingFlags
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'workspace013')
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
assert not api('material_quick_status')['busy']
api('material_shelf_open',visible=True);s=api('material_workspace_status');p=Rhino.UI.Panels.GetPanel(System.Guid(s['pages'][0]['panelId']))
flags=BindingFlags.Instance|BindingFlags.NonPublic|BindingFlags.Public
t=p.GetType().GetProperty('Tool',flags).GetValue(p);shelf=t.GetType().GetField('shelf',flags).GetValue(t)
def walk(o):
 yield o
 if hasattr(o,'Controls'):
  for c in o.Controls:
   for v in walk(c):yield v
snapshot=dict(assets=api('material_library')['assets'],bindings=api('material_inspect',objects=[str(o.Id) for o in doc.Objects]),geometry=[(str(o.Id),int(o.Geometry.DataCRC(0))) for o in doc.Objects])
button=next(c for c in walk(shelf) if c.GetType().Name=='Button' and c.Text=='AI 整理');button.GetType().GetMethod('PerformClick').Invoke(button,None)
snapshot['job']=api('material_quick_status')['shelf']['organize'];assert snapshot['job']
with open(os.path.join(folder,'organize-start.json'),'w') as f:json.dump(snapshot,f,indent=2)
print(json.dumps(dict(job=snapshot['job'],count=len(snapshot['assets']))))

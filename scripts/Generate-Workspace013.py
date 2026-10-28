"""Real ChatKit generation on the new dock tool; consumes one image request."""
import Rhino,System,clr,json,os
from System.Reflection import BindingFlags
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'workspace013');fixture=json.load(open(os.path.join(folder,'setup.json')))
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
state=api('material_quick_status');assert not state['busy'],state
assert fixture['assets'][0] in json.dumps(api('material_inspect',objects=[fixture['objects'][1]]))
api('material_tool_settings',reuseSimilar=False);api('material_workspace_open',page='materials');api('material_shelf_open',visible=False)
state=api('material_workspace_status');panel=Rhino.UI.Panels.GetPanel(System.Guid(state['pages'][0]['panelId']))
flags=BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Instance
tool=panel.GetType().GetProperty('Tool',flags).GetValue(panel);chat=tool.GetType().GetField('chat',flags).GetValue(tool);browser=chat.GetType().GetField('Browser',flags).GetValue(chat)
task=browser.CoreWebView2.ExecuteScriptAsync("window.chat.sendUserMessage({text:'生成一个全新的深蓝色哑光釉面陶瓷材质平铺贴图，均匀细微颗粒，不要砖缝、文字或场景。请生成图片。'})")
System.AppDomain.CurrentDomain.SetData('Workspace013GenerateScript',task)
report=dict(pid=EXPECTED_PID,secondTargetCorrect=True,startingAssetIds=[a['id'] for a in api('material_library')['assets']],request='one-real-image')
with open(os.path.join(folder,'generation-start.json'),'w') as f:json.dump(report,f,indent=2)
print(json.dumps(report))

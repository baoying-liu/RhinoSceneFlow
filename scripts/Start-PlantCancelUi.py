import Rhino,System,clr,json,os
from System.Reflection import BindingFlags
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
folder=os.path.join(OUTPUT_DIR,'plants015');assert os.path.isfile(os.path.join(folder,'chat-ui-verified.json'))
r=json.loads(McpApi.Execute('{"apiVersion":1,"operation":"material_workspace_status"}'))['result'];panel=Rhino.UI.Panels.GetPanel(System.Guid(r['pages'][0]['panelId']));flags=BindingFlags.Instance|BindingFlags.NonPublic|BindingFlags.Public
tool=panel.GetType().GetProperty('Tool',flags).GetValue(panel);chat=tool.GetType().GetField('chat',flags).GetValue(tool);browser=chat.GetType().GetField('Browser',flags).GetValue(chat)
before=json.loads(McpApi.Execute('{"apiVersion":1,"operation":"material_quick_status"}'))['result']['lastJob']
with open(os.path.join(folder,'cancel-ui-start.json'),'w') as f:json.dump(dict(pid=EXPECTED_PID,document=int(__rhino_doc__.RuntimeSerialNumber),before=before),f)
task=browser.CoreWebView2.ExecuteScriptAsync("window.chat.sendUserMessage({text:'生成一株 Acer palmatum 日本红枫完整透明植物素材，先核实植物物种。'}).catch(e=>console.error(String(e)))")
System.AppDomain.CurrentDomain.SetData('PlantCancelUiTask',task)
print('Real ChatKit generation requested for immediate document-close cancellation test')

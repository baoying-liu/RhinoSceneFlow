import Rhino,System,clr,json,os
from System.Reflection import BindingFlags
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
folder=os.path.join(OUTPUT_DIR,'plants015');setup=json.load(open(os.path.join(folder,'ready-start.json')))
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(__rhino_doc__.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
job=api('material_chat_status',jobId=setup['job'])
if job['status']=='running':print(json.dumps(dict(reuse=job['status'],stage=job['stage'])))
else:
 assert job['status']=='completed' and job['plantMatches'] and not job['plant'] and not job['imagePath'],job
 with open(os.path.join(folder,'visual-reuse-verified.json'),'w') as f:json.dump(job,f,indent=2)
 api('material_workspace_open',page='materials');state=api('material_workspace_status');panel=Rhino.UI.Panels.GetPanel(System.Guid(state['pages'][0]['panelId']))
 flags=BindingFlags.Instance|BindingFlags.NonPublic|BindingFlags.Public
 tool=panel.GetType().GetProperty('Tool',flags).GetValue(panel);chat=tool.GetType().GetField('chat',flags).GetValue(tool);browser=chat.GetType().GetField('Browser',flags).GetValue(chat);assert browser.CoreWebView2 is not None
 script="""(()=>{let s=window.chatkitState;if(!s?.ready)return JSON.stringify({ready:false});if(!window.plantUiTest){window.plantUiTest={started:true};window.chat.sendUserMessage({text:'请先说明如何在 Rhino 种植已入库的植物，只讨论，不要生成图片。'}).then(()=>window.plantUiTest.done=true).catch(e=>window.plantUiTest.error=String(e));}return JSON.stringify({ready:true,...window.plantUiTest});})()"""
 task=browser.CoreWebView2.ExecuteScriptAsync(script);System.AppDomain.CurrentDomain.SetData('PlantChatUiProbe',task)
 print('Actual candidate thumbnails matched; existing ChatKit user message scheduled')

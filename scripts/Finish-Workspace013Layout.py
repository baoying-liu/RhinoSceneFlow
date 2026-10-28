import Rhino,System,clr,json,os
from System.Reflection import BindingFlags
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
folder=os.path.join(OUTPUT_DIR,'workspace013');s=json.loads(McpApi.Execute('{"apiVersion":1,"operation":"material_workspace_status"}'))['result'];p=Rhino.UI.Panels.GetPanel(System.Guid(s['pages'][0]['panelId']));flags=BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Static|BindingFlags.Instance;tool=p.GetType().GetProperty('Tool',flags).GetValue(p)
assert tool.Width>=680 and tool.Content.GetType().Name=='Splitter',(tool.Width,tool.Content)
wideWidth=tool.Width
task=System.AppDomain.CurrentDomain.GetData('Workspace013NoMatch');assert task.IsCompleted and not task.IsFaulted
answer=task.Result;assert answer.MaterialRequest and len(answer.Matches)==0
asm=next(a for a in System.AppDomain.CurrentDomain.GetAssemblies() if a.GetName().Name=='Rhino.UI');registry=asm.GetType('Rhino.UI.Internal.TabPanels.TabPanelDockBars');bar=registry.GetMethod('FromDockBarId',flags).Invoke(None,System.Array[System.Object]([System.Guid(s['pages'][0]['dockBars'][0])]))
form=bar.GetType().GetMethod('HasFloatingForm',flags).Invoke(bar,System.Array[System.Object]([System.UInt32(__rhino_doc__.RuntimeSerialNumber)]));form.ClientSize=System.AppDomain.CurrentDomain.GetData('Workspace013LayoutOriginal')
report=dict(pid=EXPECTED_PID,wideDrawer=True,wideWidth=wideWidth,noForcedMatch=True,assetCount=len(list(System.IO.Directory.GetDirectories(os.path.join(folder,'library','assets')))))
with open(os.path.join(folder,'layout-verified.json'),'w') as f:json.dump(report,f,indent=2)
print(json.dumps(report))

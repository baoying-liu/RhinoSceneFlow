"""Read official ChatKit state through WebView2 SDK; no OS input."""
import System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import MaterialQuickController
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
p=MaterialQuickController.Find(__rhino_doc__.RuntimeSerialNumber);assert p is not None
flags=System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Public
chat=p.GetType().GetField('chat',flags).GetValue(p);browser=chat.GetType().GetField('Browser',flags).GetValue(chat)
assert browser.CoreWebView2 is not None
task=browser.CoreWebView2.ExecuteScriptAsync('JSON.stringify(window.chatkitState??{missing:true,body:document.body.innerText})')
System.AppDomain.CurrentDomain.SetData('SceneFlow.ChatKitProbe',task)
print('SDK probe scheduled')

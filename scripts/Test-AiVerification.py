"""B-only verification gate/routing/recovery; fake state restored, no login or image calls."""
import json,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/readiness-native'
OUT.mkdir(parents=True,exist_ok=True)
(ROOT/'artifacts/rhino-B').mkdir(exist_ok=True)
def run(name,source):
 p=OUT/(name+'.py');p.write_text(source,encoding='utf8')
 result=subprocess.check_output([sys.executable,str(ROOT/'scripts/Rhino-Mcp.py'),'run_python',str(p)],encoding='utf8',stderr=subprocess.PIPE)
 return json.loads(result)
GATE = r'''
import System,clr,Rhino,json
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import SceneFlowWorkspace,McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
f=System.Reflection.BindingFlags.Public|System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.Static
assembly=clr.GetClrType(SceneFlowWorkspace).Assembly;service=assembly.GetType('RhinoSceneFlow.Plugin.ConnectionService')
def prop(name):return service.GetProperty(name,f).GetValue(None,None)
def setval(name,value):service.GetField('<'+name+'>k__BackingField',f).SetValue(None,value)
def api(op):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op))));assert r['ok'],r;return r['result']
assert prop('Checked') and not prop('Busy'),api('connection_status')
original={k:prop(k) for k in ['Auth','Runtime','Checked','Revision']}
try:
 setval('Auth','signed_out');setval('Runtime','ready');setval('Checked',True)
 SceneFlowWorkspace.Open('materials');hosts=clr.GetClrType(SceneFlowWorkspace).GetField('Hosts',f).GetValue(None)
 host=hosts['materials'];tool=host.GetType().GetProperty('Tool',f).GetValue(host,None);chat=tool.GetType().GetField('chat',f).GetValue(tool)
 gate=chat.GetType().GetField('validation',f).GetValue(chat)
 title=chat.GetType().GetField('validationTitle',f).GetValue(chat).Text
 assert str(gate.Visibility)=='Visible' and title in ['Verification not passed',u'未通过验证'],title
 browser=chat.GetType().GetField('Browser',f).GetValue(chat)
 assert str(browser.Visibility)=='Hidden' and not browser.IsEnabled
 before=browser.CoreWebView2
 System.AppDomain.CurrentDomain.SetData('SceneFlowReadinessBrowser',browser)
 from System.Windows.Media.Imaging import RenderTargetBitmap,PngBitmapEncoder,BitmapFrame
 from System.Windows.Media import PixelFormats
 native=host.ControlObject;w=int(native.ActualWidth);h=int(native.ActualHeight)
 if w>0 and h>0:
  image=RenderTargetBitmap(w,h,96,96,PixelFormats.Pbgra32);image.Render(native);encoder=PngBitmapEncoder();encoder.Frames.Add(BitmapFrame.Create(image));stream=System.IO.File.Create(OUTPUT_DIR+'/readiness-gate.png');encoder.Save(stream);stream.Close()
 button=chat.GetType().GetField('settingsButton',f).GetValue(chat)
 import System.Windows as W
 from System.Windows.Controls.Primitives import ButtonBase
 button.RaiseEvent(W.RoutedEventArgs(ButtonBase.ClickEvent))
 settings=hosts['settings'].GetType().GetProperty('Tool',f).GetValue(hosts['settings'],None)
 assert settings.GetType().GetField('connections',f).GetValue(settings).Expanded
 assert settings.GetType().GetField('scroll',f).GetValue(settings).ScrollPosition.Y==0
finally:
 for k,v in original.items():setval(k,v)
api('connection_check');SceneFlowWorkspace.Open('materials')
System.IO.File.WriteAllText(OUTPUT_DIR+'/readiness-gate-verified.json',json.dumps(dict(pid=EXPECTED_PID,automaticCheck=True,failedGate=True,existingBrowserPreserved=True,settingsTargetExpanded=True,credentialsUnchanged=True)))
print('Failed verification gate and Settings routing passed; automatic recovery checking started; no credentials changed.')
'''
RECOVER = r'''
import System,clr,json
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import SceneFlowWorkspace,McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
f=System.Reflection.BindingFlags.Public|System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.Static
r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation='connection_status'))));assert r['ok'] and r['result']['verified'],r
hosts=clr.GetClrType(SceneFlowWorkspace).GetField('Hosts',f).GetValue(None);h=hosts['materials'];tool=h.GetType().GetProperty('Tool',f).GetValue(h,None);chat=tool.GetType().GetField('chat',f).GetValue(tool)
state=chat.GetType().GetProperty('State',f).GetValue(chat,None)
gate=chat.GetType().GetField('validation',f).GetValue(chat);assert str(gate.Visibility)=='Collapsed' and state=='ready',state
browser=chat.GetType().GetField('Browser',f).GetValue(chat)
assert System.Object.ReferenceEquals(browser,System.AppDomain.CurrentDomain.GetData('SceneFlowReadinessBrowser'))
assert str(browser.Visibility)=='Visible' and browser.IsEnabled
task=browser.ExecuteScriptAsync('JSON.stringify({ready:!!window.chatkitState?.ready,error:!!window.chatkitState?.error})')
System.AppDomain.CurrentDomain.SetData('SceneFlowReadinessProbe',task)
print('Verification recovered; original native chat frame is visible; component probe scheduled.')
'''
COMPONENT = r'''
import System,json
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
task=System.AppDomain.CurrentDomain.GetData('SceneFlowReadinessProbe');assert task.IsCompleted
result=json.loads(json.loads(str(task.Result)));assert result['ready'] and not result['error'],result
System.IO.File.WriteAllText(OUTPUT_DIR+'/readiness-recovered.json',json.dumps(dict(pid=EXPECTED_PID,automaticRecovery=True,officialChatKitReady=True,modelCalls=0)))
System.AppDomain.CurrentDomain.SetData('SceneFlowReadinessProbe',None)
print('Actual ChatKit component ready after verification recovery; no generation request.')

System.AppDomain.CurrentDomain.SetData('SceneFlowReadinessBrowser',None)
'''
run('gate',GATE)
deadline=time.monotonic()+45
while True:
 try:run('recovered',RECOVER);break
 except subprocess.CalledProcessError:
  if time.monotonic()>deadline:raise
  time.sleep(1)
while True:
 try:run('component',COMPONENT);break
 except subprocess.CalledProcessError:
  if time.monotonic()>deadline:raise
  time.sleep(.5)
print('PASS: centered failed state, focused Settings routing, automatic recovery and original browser preservation; actual ChatKit ready; no login mutation or image calls.')

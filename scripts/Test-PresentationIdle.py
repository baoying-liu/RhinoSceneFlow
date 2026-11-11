"""Observe live Eto timers between Platform commands; snapshots inside one command hide flicker."""
import importlib.machinery,json,pathlib,time,re
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/localization-02218';OUT.mkdir(exist_ok=True)
m=importlib.machinery.SourceFileLoader('idle_audit',str(ROOT/'scripts/Audit-UX20261110.py')).load_module()
prefix=r'''import Rhino,System,clr,json
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import SceneFlowWorkspace,McpApi
from Eto.Forms import UITimer
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
f=System.Reflection.BindingFlags.Public|System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.Static
hosts=clr.GetClrType(SceneFlowWorkspace).GetField('Hosts',f).GetValue(None)
def api(op,**kw):
 v=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,**kw))));assert v['ok'],v;return v['result']
'''
start=m.run(prefix+r'''
assert api('describe')['version']=='0.22.18'
d=Rhino.RhinoDoc.ActiveDoc;initial=api('plugin_settings');selected=[o.Id for o in d.Objects.GetSelectedObjects(False,False)]
api('plugin_settings',settings=dict(initial,language='en',textMode='short',showIcons=True))
SceneFlowWorkspace.Open('materials');h=hosts['materials'];tool=h.GetType().GetProperty('Tool',f).GetValue(h,None)
if h.ParentWindow is not None and isinstance(h.ParentWindow.ControlObject,System.Windows.Window):h.ParentWindow.ControlObject.Show()
target=tool.GetType().GetField('target',f).GetValue(tool)
assert target.GetType().Name=='UiLabel'
samples=System.Collections.Generic.List[System.String]();timer=UITimer();timer.Interval=.03
def sample(sender,event):samples.Add(target.Text or '')
handler=System.EventHandler[System.EventArgs](sample);timer.Elapsed+=handler;timer.Start()
state=(target,samples,timer,handler,initial,selected,d.Modified,d.Objects.Count,d.RuntimeSerialNumber)
System.AppDomain.CurrentDomain.SetData('SceneFlow_IdleRegression',state)
print('UX_AUDIT:'+json.dumps(dict(pid=EXPECTED_PID,text=target.Text)))
''')
state=r'''target,samples,timer,handler,initial,selected,modified,count,document=System.AppDomain.CurrentDomain.GetData('SceneFlow_IdleRegression')
'''
rows=[]
try:
 for language,mode in [('en','short'),('en','full'),('zh','short'),('en','short')]:
  v=m.run(prefix+state+"api('plugin_settings',settings=dict(initial,language="+repr(language)+",textMode="+repr(mode)+",showIcons=True))\nsamples.Clear()\nprint('UX_AUDIT:'+json.dumps(dict(immediate=target.Text)))")
  time.sleep(6)
  captured=m.run(prefix+state+"print('UX_AUDIT:'+json.dumps(dict(samples=list(samples),text=target.Text)))")
  assert len(captured['samples'])>100,('UI timers did not run',captured)
  assert set(captured['samples'])=={v['immediate']},(language,mode,'Text changed during idle',set(captured['samples']))
  assert bool(re.search('[\u4e00-\u9fff]',v['immediate']))==(language=='zh'),v
  rows.append(dict(language=language,mode=mode,immediate=v['immediate'],samples=len(captured['samples']),distinct=list(set(captured['samples']))))
  (OUT/'idle-stages.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
  print(json.dumps(rows[-1],ensure_ascii=False),flush=True)
 # Multiline source fragments must survive language changes without reading the rendered label.
 fragments=m.run(prefix+state+r'''
 h=hosts['materials'];tool=h.GetType().GetProperty('Tool',f).GetValue(h,None)
 status=tool.GetType().GetField('status',f).GetValue(tool)
 caption=status.GetType().GetField('caption',f).GetValue(status)
 original=caption.GetType().GetField('source',f).GetValue(caption)
 try:
  status.Text=u'材质已选中；点击应用即可。'
  status.GetType().GetMethod('Append',f).Invoke(status,System.Array[System.Object]([u'\n保存设置']))
  en=status.Text
  api('plugin_settings',settings=dict(initial,language='zh',textMode='short',showIcons=True));zh=status.Text
  api('plugin_settings',settings=dict(initial,language='en',textMode='short',showIcons=True));again=status.Text
 finally:status.Text=original
 print('UX_AUDIT:'+json.dumps(dict(en=en,zh=zh,again=again)))
'''.replace('\n ', '\n'))
 assert fragments['en']==fragments['again'] and '\n' in fragments['en'] and not re.search('[\u4e00-\u9fff]',fragments['en']),fragments
 assert re.search('[\u4e00-\u9fff]',fragments['zh']),fragments
 (OUT/'caption-fragments.json').write_text(json.dumps(fragments,ensure_ascii=False,indent=2),encoding='utf8')
 # A live selection change must be localized on the first native write.
 changed=m.run(prefix+state+r'''
d=Rhino.RhinoDoc.ActiveDoc;d.Objects.UnselectAll()
h=hosts['materials'];tool=h.GetType().GetProperty('Tool',f).GetValue(h,None)
o=next(o for o in d.Objects if not o.IsHidden and not o.IsLocked and o.IsSelectable());o.Select(True);d.Views.Redraw()
tool.GetType().GetMethod('Tick',f).Invoke(tool,None)
samples.Clear()
print('UX_AUDIT:'+json.dumps(dict(immediate=target.Text)))
''')
 assert changed['immediate']=='1 selected',changed
 time.sleep(6)
 captured=m.run(prefix+state+"print('UX_AUDIT:'+json.dumps(dict(samples=list(samples),text=target.Text)))")
 assert len(captured['samples'])>100 and set(captured['samples'])=={changed['immediate']},captured
 rows.append(dict(selectionChanged=True,immediate=changed['immediate'],samples=len(captured['samples']),distinct=list(set(captured['samples']))))
finally:
 restored=m.run(prefix+state+r'''
timer.Stop();timer.Elapsed-=handler;timer.Dispose();d=Rhino.RhinoDoc.ActiveDoc
assert d.RuntimeSerialNumber==document and d.Objects.Count==count and d.Modified==modified
d.Objects.UnselectAll()
for id in selected:
 o=d.Objects.FindId(id)
 if o is not None:o.Select(True)
api('plugin_settings',settings=initial);d.Views.Redraw()
System.AppDomain.CurrentDomain.SetData('SceneFlow_IdleRegression',None)
print('UX_AUDIT:'+json.dumps(dict(pid=EXPECTED_PID,preferencesRestored=api('plugin_settings')==initial,modelUnchanged=True)))
''')
(OUT/'idle-regression.json').write_text(json.dumps(dict(start=start,rows=rows,restored=restored),ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(dict(pid=start['pid'],cases=len(rows),samples=sum(r['samples'] for r in rows),unexpectedTransitions=0,restored=restored)))

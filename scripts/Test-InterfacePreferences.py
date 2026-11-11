"""Exercise normal Settings controls and global presentation persistence in B."""
import importlib.machinery,json,pathlib
r=pathlib.Path(__file__).resolve().parents[1];out=r/'artifacts/localization-02218'
m=importlib.machinery.SourceFileLoader('audit',str(r/'scripts/Audit-UX20261110.py')).load_module()
s=r'''import Rhino,System,clr,json
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import SceneFlowWorkspace,McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
f=System.Reflection.BindingFlags.Public|System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.Static
assembly=clr.GetClrType(SceneFlowWorkspace).Assembly
hosts=clr.GetClrType(SceneFlowWorkspace).GetField('Hosts',f).GetValue(None)
def api(op,**kw):
 value=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,**kw))));assert value['ok'],value;return value['result']
initial=api('plugin_settings');assert api('describe')['version']=='0.22.18'
SceneFlowWorkspace.Open('settings');h=hosts['settings'];tool=h.GetType().GetProperty('Tool',f).GetValue(h,None)
def field(name):return tool.GetType().GetField(name,f).GetValue(tool)
def load():tool.GetType().GetMethod('LoadDraft',f).Invoke(tool,None)
apply=assembly.GetType('RhinoSceneFlow.Plugin.WorkspaceAppearance').GetMethod('Apply',f)
try:
 load();text=field('textMode');icons=field('icons');essential=field('essentialText')
 text.SelectedKey='short';icons.SelectedKey='none';text.SelectedKey='none'
 assert icons.SelectedKey=='show' and text.SelectedKey=='none'
 essential.SelectedKey='full';icons.SelectedKey='none'
 assert text.SelectedKey=='full' and icons.SelectedKey=='none'
 essential.SelectedKey='short';text.SelectedKey='none';icons.SelectedKey='none'
 assert text.SelectedKey=='short'
 draft='UI preference draft / not saved';field('climate').Text=draft
 api('plugin_settings',settings=dict(initial,textMode='none',showIcons=True))
 apply.Invoke(None,System.Array[System.Object]([h]))
 assert field('climate').Text==draft and text.SelectedKey=='none'
 from Eto.Forms import Button
 api('plugin_settings',settings=dict(initial,textMode='full',showIcons=True,theme='light'))
 apply.Invoke(None,System.Array[System.Object]([h]));b=next(c for c in h.Children if isinstance(c,Button) and c.Image is not None);light=b.Image
 api('plugin_settings',settings=dict(initial,textMode='full',showIcons=True,theme='dark'))
 apply.Invoke(None,System.Array[System.Object]([h]));dark=b.Image
 assert not System.Object.ReferenceEquals(light,dark),'Theme icon did not change'
finally:
 api('plugin_settings',settings=initial);load();apply.Invoke(None,System.Array[System.Object]([h]))
print('UX_AUDIT:'+json.dumps(dict(pid=EXPECTED_PID,constraintEvents=True,draftPreserved=True,themeIcons=True,preferencesRestored=api('plugin_settings')==initial)))
'''
v=m.run(s);out.mkdir(exist_ok=True);(out/'native-settings-events.json').write_text(json.dumps(v,indent=2));print(json.dumps(v))

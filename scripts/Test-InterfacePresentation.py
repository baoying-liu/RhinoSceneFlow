"""B-only registered native-panel presentation regression; no mouse input."""
import pathlib,importlib.machinery,json,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/localization-02218';OUT.mkdir(exist_ok=True)
m=importlib.machinery.SourceFileLoader('ui_audit',str(ROOT/'scripts/Audit-UX20261110.py')).load_module()
source=r'''import Rhino,System,clr,json
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import SceneFlowWorkspace
from Eto.Forms import Scrollable,DropDown,Button,Expander,Label
from System.Windows.Media import VisualTreeHelper
from System.Windows.Controls import ScrollViewer
from System.Windows import Point
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
f=System.Reflection.BindingFlags.Public|System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Static|System.Reflection.BindingFlags.Instance
hosts=clr.GetClrType(SceneFlowWorkspace).GetField('Hosts',f).GetValue(None)


from RhinoSceneFlow.Plugin import McpApi,PluginPreferences
from RhinoSceneFlow.Core import MaterialLibrary
from Eto.Forms import TextBox,NumericStepper,CheckBox
assembly=clr.GetClrType(SceneFlowWorkspace).Assembly
appearance=assembly.GetType('RhinoSceneFlow.Plugin.WorkspaceAppearance').GetMethod('Apply',f)
def api(op,**kw):
 return json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,**kw))))
def apply(h):appearance.Invoke(None,System.Array[System.Object]([h]));h.ControlObject.UpdateLayout()
assert api('describe')['result']['version']=='0.22.18'
initial=api('plugin_settings')['result']
d=Rhino.RhinoDoc.ActiveDoc
before=dict(path=d.Path,count=d.Objects.Count,modified=d.Modified,selection=[str(x.Id) for x in d.Objects.GetSelectedObjects(False,False)])
results=[]
try:
 bad=dict(initial,textMode='none',showIcons=False)
 assert not api('plugin_settings',settings=bad)['ok']
 assert api('plugin_settings')['result']==initial
 assert len([n for n in assembly.GetManifestResourceNames() if '.InterfaceIcons.' in n and n.endswith('.png')])==248
 for page in ['settings','post','uv','library','planting','plantsList','properties','materials','export']:
  SceneFlowWorkspace.Open(page);h=hosts[page]
  # Sandbox startup can leave the registered floating form hidden in WPF.
  # Show its existing native window; never create/reparent a test panel.
  if h.ParentWindow is not None and isinstance(h.ParentWindow.ControlObject,System.Windows.Window):h.ParentWindow.ControlObject.Show()
  expanders=[c for c in h.Children if isinstance(c,Expander)]
  expanded=[c.Expanded for c in expanders]
  try:
   for c in expanders:c.Expanded=True
   base=dict(initial,language='en',textMode='full',showIcons=True)
   assert api('plugin_settings',settings=base)['ok'];apply(h)
   controls=list(h.Children)
   text0=[(c,str(c.Text)) for c in controls if isinstance(c,(Label,Button,CheckBox))]
   values=[(c,str(c.Text)) for c in controls if isinstance(c,TextBox)]
   dropdowns=[(c,[(str(i.Key),str(i.Text)) for i in c.Items]) for c in controls if isinstance(c,DropDown)]
   for mode,icons,essential in [('short',True,'short'),('short',False,'short'),('none',True,'short'),('none',True,'full'),('full',False,'short'),('full',True,'short')]:
    assert api('plugin_settings',settings=dict(base,textMode=mode,showIcons=icons,essentialTextMode=essential))['ok'];apply(h)
    buttons=[c for c in controls if isinstance(c,Button)]
    if not icons:assert all(c.Image is None for c in buttons),[(page,str(c.Text),str(c.Tag),str(c.Image)) for c in buttons if c.Image is not None]
    compact=[c for c in buttons if not c.Text and c.Image is not None]
    for c in compact:assert c.ToolTip and (mode!='none' or not c.ControlObject.IsVisible or 0<c.ControlObject.ActualWidth<=40),(page,mode,c.Text,c.ControlObject.ActualWidth,c.ToolTip)
    assert all(str(c.Text)==v for c,v in values),'Edited values changed'
    issues=[];visible=0
    for c in controls:
     n=c.ControlObject
     if isinstance(c,(Button,DropDown,NumericStepper,TextBox,CheckBox,Label)) and isinstance(n,System.Windows.FrameworkElement) and n.IsVisible and n.ActualWidth>0:
      visible+=1
    assert visible>3,(page,'No visible controls')
    if mode=='none' and essential=='full':assert all([(str(i.Key),str(i.Text)) for i in c.Items]==v for c,v in dropdowns),'Essential full dropdown text changed: '+page
    layout=[]
    try:
     for width in [280,360,480]:
      h.ControlObject.Width=width;h.ControlObject.UpdateLayout();issues=[]
      for c in controls:
       n=c.ControlObject
       if isinstance(c,(Button,DropDown,NumericStepper,TextBox,CheckBox,Label)) and isinstance(n,System.Windows.FrameworkElement) and n.IsVisible and n.ActualWidth>0:
        pt=n.TranslatePoint(Point(0,0),h.ControlObject)
        if pt.X < -1 or pt.X+n.ActualWidth>width+1:issues.append(dict(type=str(c.GetType()),text=c.Text if hasattr(c,'Text') else '',x=pt.X,width=n.ActualWidth))
      layout.append(dict(width=width,issues=issues))
    finally:h.ControlObject.Width=System.Double.NaN;h.ControlObject.UpdateLayout()
    results.append(dict(layout=layout,page=page,textMode=mode,icons=icons,essential=essential,buttons=len(buttons),compact=len(compact),visible=visible))
   assert all(str(c.Text)==text for c,text in text0),'Full labels failed to restore: '+page
   assert all([(str(i.Key),str(i.Text)) for i in c.Items]==v for c,v in dropdowns),'Dropdown labels failed to restore: '+page
  finally:
   for c,value in zip(expanders,expanded):
    if not c.IsDisposed:c.Expanded=value
 assert all(row['compact']>0 for row in results if row['textMode']=='none'),results
finally:
 assert api('plugin_settings',settings=initial)['ok']
 SceneFlowWorkspace.Open('settings')
 if hosts['settings'].ParentWindow is not None and isinstance(hosts['settings'].ParentWindow.ControlObject,System.Windows.Window):hosts['settings'].ParentWindow.ControlObject.Show()
 apply(hosts['settings'])
after=dict(path=d.Path,count=d.Objects.Count,modified=d.Modified,selection=[str(x.Id) for x in d.Objects.GetSelectedObjects(False,False)])
assert before==after,(before,after)
print('UX_AUDIT:'+json.dumps(dict(version='0.22.18',pid=EXPECTED_PID,before=before,after=after,rows=results,invalidPairRejected=True,resources=248,assembly=assembly.Location)))
'''
language=sys.argv[1] if len(sys.argv)>1 else 'en'
assert language in ['en','zh']
source=source.replace("language='en'",'language='+repr(language))
v=m.run(source);v['language']=language;(OUT/('native-presentation-'+language+'.json')).write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
assert all(not w['issues'] for x in v['rows'] for w in x['layout']), 'Native layout overflow; inspect saved report'
print(json.dumps(dict(version=v['version'],pid=v['pid'],language=language,cases=len(v['rows']),layoutIssues=sum(len(w['issues']) for x in v['rows'] for w in x['layout']),resources=v['resources'],invalidPairRejected=v['invalidPairRejected'],assembly=v['assembly'])))

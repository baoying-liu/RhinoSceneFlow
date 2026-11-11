"""Verify actual captions and image geometry, not just control roundtrips."""
import importlib.machinery,json,pathlib
r=pathlib.Path(__file__).resolve().parents[1];out=r/'artifacts/localization-02218';out.mkdir(exist_ok=True)
m=importlib.machinery.SourceFileLoader('audit',str(r/'scripts/Audit-UX20261110.py')).load_module()
s=r'''import Rhino,System,clr,json,re
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import SceneFlowWorkspace,McpApi
from Eto.Forms import Label,Button,CheckBox,Expander,DropDown,GridView
from System.Windows.Controls import Image
from System.Windows.Media import VisualTreeHelper
from System.Windows import Rect
f=System.Reflection.BindingFlags.Public|System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.Static
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
hosts=clr.GetClrType(SceneFlowWorkspace).GetField('Hosts',f).GetValue(None)
def api(op,**kw):
 v=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,**kw))));assert v['ok'],v;return v['result']
assert api('describe')['version']=='0.22.18'
initial=api('plugin_settings');d=Rhino.RhinoDoc.ActiveDoc
before=dict(count=d.Objects.Count,modified=d.Modified,selected=[str(o.Id) for o in d.Objects.GetSelectedObjects(False,False)])
results=[];errors=[];imageRows=[]
def imgs(n,button,page,text):
 for i in range(VisualTreeHelper.GetChildrenCount(n)):
  c=VisualTreeHelper.GetChild(n,i)
  if isinstance(c,Image) and c.IsVisible and c.ActualWidth>0:
   rect=c.TransformToAncestor(button).TransformBounds(Rect(0,0,c.ActualWidth,c.ActualHeight))
   imageRows.append(dict(page=page,text=text,width=c.ActualWidth,height=c.ActualHeight,renderWidth=rect.Width,renderHeight=rect.Height,requested=c.Width,sourceWidth=c.Source.Width))
   assert rect.Width<=17 and rect.Height<=17,(page,text,'Stretched icon',rect.Width,rect.Height)
  imgs(c,button,page,text)
try:
 for page in ['settings','materials','library','uv','planting','plantsList','properties','export','post']:
  SceneFlowWorkspace.Open(page);h=hosts[page]
  if h.ParentWindow is not None and isinstance(h.ParentWindow.ControlObject,System.Windows.Window):h.ParentWindow.ControlObject.Show()
  expanders=[c for c in h.Children if isinstance(c,Expander)];expanded=[c.Expanded for c in expanders]
  try:
   for c in expanders:c.Expanded=True
   texts={}
   for mode in ['full','short','none','full']:
    api('plugin_settings',settings=dict(initial,language='en',textMode=mode,showIcons=True,essentialTextMode='short'))
    h.ControlObject.UpdateLayout();captions=[]
    for c in h.Children:
     if isinstance(c,(Label,Button,CheckBox)):
      t=c.Text or ''
      if c.Tag!='user-content':
       captions.append(t)
       checked=t
       if c.Tag=='localized-context':
        for obj in d.Objects:
         if obj.Name:checked=checked.replace(obj.Name,'<object name>')
       if re.search(u'[\u4e00-\u9fff]',checked):errors.append(dict(page=page,mode=mode,text=t,type=str(c.GetType())))
     if isinstance(c,DropDown) and c.Tag!='user-content':
      for item in c.Items:
       if c.Tag=='catalog-values' and item.Key:continue
       if item.Key=='zh':continue
       if re.search(u'[\u4e00-\u9fff]',item.Text):errors.append(dict(page=page,mode=mode,item=item.Text,key=item.Key))
     if isinstance(c,GridView):
      for column in c.Columns:
       if re.search(u'[\u4e00-\u9fff]',column.HeaderText or ''):errors.append(dict(page=page,column=column.HeaderText))
     if isinstance(c,Button) and c.Image is not None:imgs(c.ControlObject,c.ControlObject,page,c.Text)
    if mode in ['full','short']:texts[mode]=captions
    results.append(dict(page=page,mode=mode,captions=captions))
   assert texts['full']!=texts['short'],(page,'No abbreviation effect')
   if page=='post':assert 'Open AI render studio' in texts['full'] and 'Open Studio' in texts['short']
   if page=='uv':assert 'Physical-scale UVs' in texts['full'] and 'World UV' in texts['short']
  finally:
   for c,v in zip(expanders,expanded):
    if not c.IsDisposed:c.Expanded=v
 # Real dropdown events: no SaveDraft invocation and no saving climate drafts.
 SceneFlowWorkspace.Open('settings');h=hosts['settings'];tool=h.GetType().GetProperty('Tool',f).GetValue(h,None)
 def field(name):return tool.GetType().GetField(name,f).GetValue(tool)
 tool.GetType().GetMethod('LoadDraft',f).Invoke(tool,None)
 field('climate').Text='Unsaved region test'
 field('language').SelectedKey='en';field('textMode').SelectedKey='short'
 assert api('plugin_settings')['textMode']=='short' and api('plugin_settings')['language']=='en'
 assert api('plugin_settings')['climate']==initial['climate'] and field('climate').Text=='Unsaved region test'
 field('textMode').SelectedKey='none';field('icons').SelectedKey='none'
 assert api('plugin_settings')['textMode']=='short' and api('plugin_settings')['showIcons']==False
 tool.GetType().GetMethod('LoadDraft',f).Invoke(tool,None)
 assert api('plugin_settings')['textMode']=='short','Discard reverted an applied appearance setting'
finally:
 api('plugin_settings',settings=initial)
 SceneFlowWorkspace.Open('settings');h=hosts['settings'];tool=h.GetType().GetProperty('Tool',f).GetValue(h,None);tool.GetType().GetMethod('LoadDraft',f).Invoke(tool,None)
 if h.ParentWindow is not None and isinstance(h.ParentWindow.ControlObject,System.Windows.Window):h.ParentWindow.ControlObject.Show()
after=dict(count=d.Objects.Count,modified=d.Modified,selected=[str(o.Id) for o in d.Objects.GetSelectedObjects(False,False)])
assert before==after,(before,after)
print('UX_AUDIT:'+json.dumps(dict(pid=EXPECTED_PID,errors=errors,rows=results,images=imageRows,instantApply=True,otherDraftPreserved=True,before=before,after=after)))
'''
v=m.run(s);(out/'actual-language-icons.json').write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8')
assert not v['errors'],v['errors']
assert len(v['images'])>30,'No actual image measurements'
print(json.dumps(dict(pid=v['pid'],pages=9,states=len(v['rows']),chineseUiLabels=len(v['errors']),measuredIcons=len(v['images']),largestIcon=max(max(x['renderWidth'],x['renderHeight']) for x in v['images']),instantApply=v['instantApply'],otherDraftPreserved=v['otherDraftPreserved'])))

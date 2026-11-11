"""B-only live library language, filter, draft and tooltip regression. No image generation."""
import pathlib,importlib.machinery,json,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/localization-02218';OUT.mkdir(exist_ok=True)
m=importlib.machinery.SourceFileLoader('library_language_audit',str(ROOT/'scripts/Audit-UX20261110.py')).load_module()
s=r'''import Rhino,System,clr,json,re
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import SceneFlowWorkspace,McpApi,CatalogService
from Eto.Forms import Label,Button,CheckBox,TextBox,DropDown,GridView,GroupBox
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
f=System.Reflection.BindingFlags.Public|System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.Static
hosts=clr.GetClrType(SceneFlowWorkspace).GetField('Hosts',f).GetValue(None)
def api(op,**kw):
 v=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,**kw))));assert v['ok'],v;return v['result']
def field(obj,key):return obj.GetType().GetField(key,f).GetValue(obj)
assert api('describe')['version']=='0.22.18'
d=Rhino.RhinoDoc.ActiveDoc;before=dict(count=d.Objects.Count,modified=d.Modified,selected=[str(o.Id) for o in d.Objects.GetSelectedObjects(False,False)])
initial=api('plugin_settings');assets=api('material_library')['assets'];plants=api('plant_library')['assets']
assert all('en' in a['localizations'] and 'zh' in a['localizations'] for a in assets+plants)
jobStore=clr.GetClrType(CatalogService).GetField('jobs',f).GetValue(None);jobCount=jobStore.Count
assert api('material_catalog_localize')['job'] is None and api('plant_catalog_localize')['job'] is None
SceneFlowWorkspace.Open('library');h=hosts['library'];tool=h.GetType().GetProperty('Tool',f).GetValue(h,None);shelf=field(tool,'shelf')
query=field(shelf,'search');category=field(shelf,'category');tag=field(shelf,'tag');name=field(shelf,'name')
old=dict(query=query.Text,category=category.SelectedKey,tag=tag.SelectedKey,name=name.Text)
asset=next(a for a in assets if a['tags'] and a['localizations']['en']['tags'][a['tags'][0]]!=a['tags'][0])
rows=[];issues=[]
try:
 category.SelectedKey=asset['category'];tag.SelectedKey=asset['tags'][0];query.Text=asset['localizations']['en']['tags'][asset['tags'][0]]
 name.Text='Unsaved source-name draft / do not save'
 expected={str(row[2]) for row in field(shelf,'rows')};assert asset['id'] in expected
 for lang in ['en','zh','en']:
  api('plugin_settings',settings=dict(initial,language=lang,textMode='full',showIcons=True))
  assert query.Text==asset['localizations']['en']['tags'][asset['tags'][0]] and category.SelectedKey==asset['category'] and tag.SelectedKey==asset['tags'][0]
  assert {str(row[2]) for row in field(shelf,'rows')}==expected
  assert name.Text=='Unsaved source-name draft / do not save'
  for row in field(shelf,'rows'):
   a=next(a for a in assets if a['id']==str(row[2]));t=a['localizations'][lang]
   assert row[1]==t['name']+'\n'+t['category'],(lang,row[1],t)
  catText=category.SelectedValue.Text;tagText=tag.SelectedValue.Text
  assert catText==next(a['localizations'][lang]['category'] for a in assets if a['category']==asset['category'])
  assert tagText in [a['localizations'][lang]['tags'][asset['tags'][0]] for a in assets if asset['tags'][0] in a['tags']]
  rows.append(dict(language=lang,categoryKey=category.SelectedKey,categoryText=catText,tagKey=tag.SelectedKey,tagText=tagText,matched=len(expected)))
 for page in ['settings','materials','library','uv','planting','plantsList','properties','export','post']:
  SceneFlowWorkspace.Open(page);host=hosts[page]
  if host.ParentWindow is not None and isinstance(host.ParentWindow.ControlObject,System.Windows.Window):host.ParentWindow.ControlObject.Show()
  for c in host.Children:
   def check(kind,text):
    if not text:return
    if c.Tag=='localized-context':
     for obj in d.Objects:
      if obj.Name:text=text.replace(obj.Name,'<object name>')
    if re.search(u'[\u4e00-\u9fff]',text):issues.append(dict(page=page,kind=kind,text=text))
   if isinstance(c,(Label,Button,CheckBox,GroupBox)) and c.Tag!='user-content':check('caption',c.Text)
   if isinstance(c,(Label,Button,CheckBox,GroupBox,TextBox)):check('tooltip',c.ToolTip)
   if isinstance(c,TextBox):check('placeholder',c.PlaceholderText)
   if isinstance(c,DropDown):
    for item in c.Items:
     if item.Key=='zh':continue
     if c.Tag=='user-content':continue
     check('choice',item.Text)
 assert not issues,issues
 assert not CatalogService.Busy and jobStore.Count==jobCount,'Language switching launched AI metadata work'
finally:
 query.Text=old['query'];category.SelectedKey=old['category'];tag.SelectedKey=old['tag'];name.Text=old['name'];api('plugin_settings',settings=initial)
 SceneFlowWorkspace.Open('library')
after=dict(count=d.Objects.Count,modified=d.Modified,selected=[str(o.Id) for o in d.Objects.GetSelectedObjects(False,False)])
assert before==after,(before,after)
print('UX_AUDIT:'+json.dumps(dict(pid=EXPECTED_PID,materials=len(assets),plants=len(plants),rows=rows,issues=issues,draftPreserved=True,filtersPreserved=True,noAiOnSwitch=True,before=before,after=after,materialDirectory=api('material_library')['directory'],plantDirectory=api('plant_library')['directory'])))
'''
# Exact asset JSON bytes must stay unchanged while reading/switching languages.
base=json.loads((OUT/'source-assets-before.json').read_text(encoding='utf8'))
def hashes():return {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for kind in ['materials','plants'] for p in (pathlib.Path(base[kind]['directory'])/'assets').glob('*/asset.json')}
before=hashes();v=m.run(s);after=hashes();assert before==after,'Language switch wrote asset metadata'
v['assetFilesUnchanged']=True;(OUT/'library-language-regression.json').write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:v[k] for k in ['pid','materials','plants','draftPreserved','filtersPreserved','noAiOnSwitch','assetFilesUnchanged','issues']}))

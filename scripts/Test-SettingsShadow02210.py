"""B-only settings UI / owned export checks through the original Rhino Platform.
Run after deployment: python -X utf8 scripts/Test-SettingsShadow02210.py ui|export
Never opens or replaces the active document. Export uses copies of view settings.
"""
import importlib.machinery,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/settings-shadow-02210'
OUT.mkdir(exist_ok=True)
audit=importlib.machinery.SourceFileLoader('settings_shadow_audit',str(ROOT/'scripts/Audit-UX20261110.py')).load_module()
prefix="""import Rhino,System,clr,json
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi,SceneFlowWorkspace,PlantService,PluginPreferences,WorkbenchService,WorkbenchPlan
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
d=Rhino.RhinoDoc.ActiveDoc
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(d.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
assert api('describe')['version']=='0.22.10'
"""
if sys.argv[1]=='ui':
 source=prefix+"""
for page in ['materials','library','uv','planting','plantsList','properties','export','post','settings']:api('material_workspace_open',page=page)
state=api('material_workspace_status')
assert len(state['pages'])==9 and all(t['error'] is None for t in state['tools'].values()),state
flags=System.Reflection.BindingFlags.Static|System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.Public|System.Reflection.BindingFlags.NonPublic
hosts=clr.GetClrType(SceneFlowWorkspace).GetField('Hosts',flags).GetValue(None)
host=hosts['settings'];tool=host.GetType().GetProperty('Tool',flags).GetValue(host,None);typ=tool.GetType()
field=lambda key:typ.GetField(key,flags).GetValue(tool)
load=typ.GetMethod('LoadDraft',flags)
saved=PluginPreferences.Load();billboards=PlantService.Settings;original=billboards.PlanHeightRatio
def click(button):button.GetType().GetMethod('OnClick',flags).Invoke(button,System.Array[System.Object]([System.EventArgs.Empty]))
try:
 field('ratio').Value=original+.01
 assert PlantService.Settings.PlanHeightRatio==original,'Draft changed live settings before Save'
 click(field('save'))
 assert abs(PlantService.Settings.PlanHeightRatio-original-.01)<1e-10,'Save did not apply'
 field('mode').SelectedKey='auto';field('angle').Value=79;field('plan').Value=20
 click(field('save'))
 assert abs(PlantService.Settings.PlanHeightRatio-original-.01)<1e-10
 assert field('save').Enabled and field('feedback').Text,'Invalid settings did not retain editable draft'
 load.Invoke(tool,None)
 assert not field('save').Enabled,'Discard left pending controls'
finally:
 PluginPreferences.Save(saved);PlantService.Settings=billboards;load.Invoke(tool,None)
print('UX_AUDIT:'+json.dumps(dict(pid=EXPECTED_PID,path=d.Path,modified=d.Modified,workspace=api('material_workspace_status'),settingsUi=True)))
"""
 result=audit.run(source);(OUT/'native-ui.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
 print(json.dumps(dict(pid=result['pid'],settingsUi=result['settingsUi'],pages=len(result['workspace']['pages']))))
elif sys.argv[1]=='export':
 for name,separate,grouping,plants,visible in [('species',True,'species',True,True),('individual',True,'individual',True,True),('all',True,'all',True,True),('combined',False,'species',True,True),('no-plants',True,'species',False,True),('hidden-shadow',True,'species',True,False)]:
  target=str(OUT/(name+'.psd'))
  source=prefix+"""
from RhinoSceneFlow.Core import MaterialLibrary
from RhinoSceneFlow.Plugin import ExportLayerSetting
from System.Collections.Generic import List
row=WorkbenchService.Settings(d)[0].Copy();row.Width=480;row.Height=360;row.Included=True;row.PlantShadows=True;row.SeparatePlantShadows=SEPARATE
shadow=ExportLayerSetting();shadow.Kind='shadow';shadow.Blend='mul ';shadow.Opacity=45;shadow.Visible=VISIBLE
texture=ExportLayerSetting();texture.Kind='texture'
layers=[shadow,texture]
if PLANTS:
 foliage=ExportLayerSetting();foliage.Kind='plants';foliage.PlantGrouping=GROUPING;layers.insert(0,foliage)
row.Layers=List[ExportLayerSetting](layers);row.Validate()
assert not System.IO.File.Exists(TARGET),'Retain existing test evidence rather than overwriting it'
report=WorkbenchService.Export(d,System.Array[WorkbenchPlan]([WorkbenchPlan(row,TARGET,False)]))
settings=System.Text.Json.JsonSerializer.Serialize(report,MaterialLibrary.Json)
print('UX_AUDIT:'+json.dumps(dict(report=json.loads(settings),modified=d.Modified)))
""".replace('SEPARATE',repr(separate)).replace('VISIBLE',repr(visible)).replace('PLANTS',repr(plants)).replace('GROUPING',repr(grouping)).replace('TARGET',repr(target))
  result=audit.run(source);(OUT/(name+'-report.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(name,json.dumps(result,ensure_ascii=False))
else:raise ValueError('ui | export')

"""After native Open and UI ticks, verify persistence, exercise property UI queue and save evidence."""
import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi,ExportPanelController
from System.Reflection import BindingFlags
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'properties017');record=json.load(open(os.path.join(folder,'setup.json')))
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
assert doc.Path==record['model'],doc.Path
state=api('plant_group_state',groupId=record['group']);assert not state['busy'] and not state['error'] and state['count']==32,state
obj=doc.Objects.FindId(System.Guid(record['group']));rows=json.loads(obj.Geometry.UserDictionary.GetString('SceneFlow.PlantRows.v1'));row=next(r for r in rows if r['id']==record['individual'])
assert row['scale']==2.1 and row['mirror'] and row['asset']==record['individualAsset'] and abs(row['position']['z']-1.8)<1e-5,row
for page in ['materials','library','uv','planting','export','plantsList','properties']:api('material_workspace_open',page=page)
workspace=api('material_workspace_status');assert len(workspace['pages'])==7 and all(t['error'] is None for t in workspace['tools'].values()),workspace
api('plant_group_manage',groups=[record['group']],locked=True)
api('plant_group_manage',groups=[record['group']],visible=False)
api('plant_group_manage',groups=[record['group']],visible=True)
assert doc.Objects.FindId(System.Guid(record['group'])).IsLocked,'Hide/show lost lock state'
api('plant_group_manage',groups=[record['group']],locked=False)
# Create a real named view and export plants using all three grouping modes.
vp=doc.Views.ActiveView.ActiveViewport;vp.SetCameraLocation(Rhino.Geometry.Point3d(40,-35,30),False);vp.SetCameraTarget(Rhino.Geometry.Point3d(12,10,3),False);vp.ZoomExtents()
index=doc.NamedViews.Add('Properties 017',vp.Id);view=str(doc.NamedViews[index].NamedViewId)
ExportPanelController.Open(doc).RefreshNamedViews()
exports=[]
for grouping in ['individual','species','all']:
 api('configure_view',viewId=view,settings=dict(width=320,height=240,layers=[dict(kind='plants',plantGrouping=grouping),dict(kind='shadow',blend='mul '),dict(kind='material')],plantShadows=True))
 rep=api('export_workbench',directory=os.path.join(folder,'PSD-'+grouping),views=[view],collision='overwrite');assert all(f['ok'] for f in rep['files']),rep;exports.append(rep)
doc.Objects.UnselectAll();doc.Objects.Select(System.Guid(record['objects'][0]));api('material_workspace_open',page='properties')
record.update(pid=EXPECTED_PID,nativeReopen=True,allSevenToolsHealthy=True,hideShowPreservesLock=True,exports=exports,view=view)
with open(os.path.join(folder,'verified.json'),'w') as f:json.dump(record,f,indent=2)
print(json.dumps(dict(pid=EXPECTED_PID,version='0.17.0',persistedCustom=True,exportGroups=3,tools=7)))

import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi,WorkbenchService
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'plants015');setup=json.load(open(os.path.join(folder,'setup.json')))
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
# A camera that fits the full billboards; native ZoomExtents may not refresh an initial conduit bbox until a draw.
vp=doc.Views.ActiveView.ActiveViewport;vp.SetCameraLocations(Rhino.Geometry.Point3d(0,2,2),Rhino.Geometry.Point3d(8,-15,9));vp.ZoomBoundingBox(Rhino.Geometry.BoundingBox(Rhino.Geometry.Point3d(-5,-1,0),Rhino.Geometry.Point3d(5,8,5)))
info=Rhino.DocObjects.ViewInfo(vp);info.Name='Plant015 Perspective';idx=doc.NamedViews.Add(info);view=str(doc.NamedViews[idx].NamedViewId);info.Dispose();setup['view']=view
with open(os.path.join(folder,'setup.json'),'w') as f:json.dump(setup,f,indent=2)
before=dict(modified=doc.Modified,selection=[str(o.Id) for o in doc.Objects.GetSelectedObjects(False,False)],count=doc.Objects.Count)
reports={}
for grouping in ['individual','species','all']:
 api('configure_view',viewId=view,settings=dict(width=600,height=400,layers=[dict(kind='plants',plantGrouping=grouping),dict(kind='texture'),dict(kind='material')]))
 report=api('export_workbench',directory=os.path.join(folder,grouping),views=[view]);assert all(f['ok'] for f in report['files']),report;reports[grouping]=report
after=dict(modified=doc.Modified,selection=[str(o.Id) for o in doc.Objects.GetSelectedObjects(False,False)],count=doc.Objects.Count);assert before==after
row=next(r for r in WorkbenchService.Settings(doc) if str(r.Id)==view);row.Mode=System.Guid(next(m for m in api('workbench_settings')['displayModes'] if m['name']=='Rendered')['id']);bitmap=WorkbenchService.Preview(doc,row,720);bitmap.Save(os.path.join(folder,'native-fit.png'),System.Drawing.Imaging.ImageFormat.Png);bitmap.Dispose()
with open(os.path.join(folder,'exports.json'),'w') as f:json.dump(dict(pid=EXPECTED_PID,reports=reports,readOnly=True,ai=api('material_chat_status',jobId=setup['aiJob'])),f,indent=2)
print(json.dumps(dict(exported=list(reports.keys()),readOnly=True,ai=api('material_chat_status',jobId=setup['aiJob'])['status'])))

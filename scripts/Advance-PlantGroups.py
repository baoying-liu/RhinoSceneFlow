import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi,WorkbenchService
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'plants016');setup=json.load(open(os.path.join(folder,'setup.json')))
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
root=setup['group'];path=os.path.join(folder,'phases.json');record=json.load(open(path)) if os.path.isfile(path) else dict(phase=0)
state=api('plant_group_state',groupId=root);assert not state['busy'] and state['error'] is None,state
objects=api('plant_instances')['objects'];settings=state['spec']['settings'];phase=record['phase']
def positions(rows):return {p['id']:p['position'] for p in rows}
if phase==0:
 record['baseline']=objects;settings['sizeSeed']=930;api('plant_group_update',groupId=root,settings=settings)
elif phase==1:
 assert positions(objects)==positions(record['baseline']);assert any(a['scaleWidth']!=b['scaleWidth'] for a,b in zip(objects,record['baseline']))
 record['sizeSeedIndependent']=True;settings['mirrorSeed']=831;api('plant_group_update',groupId=root,settings=settings)
elif phase==2:
 assert positions(objects)==positions(record['baseline']);record['mirrorSeedIndependent']=True
 mesh=doc.Objects.FindId(System.Guid(setup['surface'])).Geometry.DuplicateMesh()
 for i in range(mesh.Vertices.Count):
  v=mesh.Vertices[i];mesh.Vertices.SetVertex(i,v.X,v.Y,v.X*.2)
 mesh.Normals.ComputeNormals();undo=doc.BeginUndoRecord('Owned carrier slope change')
 try:assert doc.Objects.Replace(System.Guid(setup['surface']),mesh)
 finally:
  mesh.Dispose()
  if undo:doc.EndUndoRecord(undo)
elif phase==3:
 assert all(abs(p['position']['z']-p['position']['x']*.2)<1e-5 for p in objects),objects[:3]
 assert state['manual']==2;record['slopeAndManualFollow']=True;assert doc.Undo()
elif phase==4:
 assert all(abs(p['position']['z'])<1e-6 for p in objects);record['carrierUndo']=True
 doc.Objects.UnselectAll();doc.Objects.Select(System.Guid(root));api('material_workspace_open',page='planting')
 assert Rhino.RhinoApp.RunScript('_RhinoSceneFlowPlant 8,5,0 9,5,0 _Enter',False)
elif phase==5:
 assert state['count']==60 and state['manual']==4,state;record['continuousNativeCommand']=True
 undo=doc.BeginUndoRecord('Owned carrier deletion')
 try:assert doc.Objects.Delete(System.Guid(setup['surface']),True)
 finally:
  if undo:doc.EndUndoRecord(undo)
elif phase==6:
 assert state['count']==60 and state['manual']==4 and doc.Objects.FindId(System.Guid(setup['surface'])) is None,state;record['deletedCarrierPreservesPlants']=True;assert doc.Undo()
elif phase==7:
 assert state['count']==60 and state['manual']==4 and doc.Objects.Count==2,state
 vp=doc.Views.ActiveView.ActiveViewport;vp.SetCameraLocation(Rhino.Geometry.Point3d(25,-25,23),False);vp.SetCameraTarget(Rhino.Geometry.Point3d(10,5,0),False);vp.ZoomExtents();doc.Views.Redraw()
 index=doc.NamedViews.Add('Parametric Planting',vp.Id);view=str(doc.NamedViews[index].Viewport.Id)
 row=next(r for r in WorkbenchService.Settings(doc) if str(r.Id)==view)
 api('configure_view',viewId=view,settings=dict(width=700,height=500,mode=str(Rhino.Display.DisplayModeDescription.RenderedId),layers=[dict(kind='plants',plantGrouping='individual'),dict(kind='shadow',blend='mul '),dict(kind='material')],plantShadows=True))
 report=api('export_workbench',directory=folder,views=[view],collision='overwrite');assert all(f['ok'] for f in report['files']),report;record['export']=report
 b=WorkbenchService.Preview(doc,row,900);b.Save(os.path.join(folder,'native.png'),System.Drawing.Imaging.ImageFormat.Png);b.Dispose()
 options=Rhino.FileIO.FileWriteOptions();options.UpdateDocumentPath=True;options.SuppressDialogBoxes=True;record['model']=os.path.join(folder,'Parametric-Plants-'+str(EXPECTED_PID)+'.3dm');assert doc.WriteFile(record['model'],options) and not doc.Modified
 record['save']=True;record['view']=view
else:raise Exception('All phases already completed')
record['phase']=phase+1
with open(path,'w') as f:json.dump(record,f,indent=2)
print(json.dumps(dict(completedPhase=phase,nextPhase=phase+1,count=state['count'],manual=state['manual'])))

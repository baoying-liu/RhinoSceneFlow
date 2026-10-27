"""B-only opaque albedo integration; unique fixtures, exact export-state preservation."""
import Rhino,System,clr,json,os
from Rhino.Geometry import Point3d,Vector3d,Plane,Interval,Brep,Box,Circle,Cylinder,Sphere,BoundingBox
from System.Drawing import Bitmap,Color
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi,ExportPanelController,WorkbenchService
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'textures');os.makedirs(folder,exist_ok=True)
def raw(op,**kw):return json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
def api(op,**kw):
 r=raw(op,**kw);assert r['ok'],r;return r['result']
assert api('describe')['version']=='0.10.0'
def state():
 v=doc.Views.ActiveView.ActiveViewport
 return (doc.Modified,tuple((str(o.Id),int(o.Geometry.DataCRC(0)),(o.Attributes.Name,o.Attributes.LayerIndex,str(o.Attributes.MaterialSource),o.Attributes.MaterialIndex,tuple((k,o.Attributes.GetUserString(k)) for k in o.Attributes.GetUserStrings().AllKeys),str(o.GetRenderMaterial(True).Id) if o.GetRenderMaterial(True) else None)) for o in doc.Objects),str(v.CameraLocation),str(v.CameraDirection),str(v.CameraUp),str(v.Size),v.Name,str(v.DisplayMode.Id),int(doc.RenderSettings.Sun.Hash),tuple(str(o.Id) for o in doc.Objects.GetSelectedObjects(False,False)),tuple(str(v.MainViewport.Id) for v in doc.Views.GetViewList(True,True)))
tag='TextureTest_'+str(System.Guid.NewGuid())[:8];ids=[];layers=[];views=[];originalModified=doc.Modified;originalRedraw=doc.Views.RedrawEnabled;doc.Views.RedrawEnabled=False
scale=Rhino.RhinoMath.UnitScale(Rhino.UnitSystem.Meters,doc.ModelUnitSystem)
def p(x,y,z):return Point3d((100+x)*scale,(100+y)*scale,z*scale)
def layer(name):
 l=Rhino.DocObjects.Layer();l.Name=tag+name;i=doc.Layers.Add(l);layers.append(doc.Layers[i].Id);return i
def add(name,geometry,li):
 a=Rhino.DocObjects.ObjectAttributes();a.Name=name;a.LayerIndex=li;a.SetUserString('SceneFlow.TextureTest',tag)
 id=doc.Objects.Add(geometry,a);assert id!=System.Guid.Empty;ids.append(id);return str(id)
def plane(x,y,w,h,z,li,name):return add(name,Brep.CreateFromCornerPoints(p(x,y,z),p(x+w,y,z),p(x+w,y+h,z),p(x,y+h,z),doc.ModelAbsoluteTolerance),li)
report=dict(pid=EXPECTED_PID,version='0.10.0',assembly=clr.GetClrType(McpApi).Assembly.Location,tag=tag,exports={})
try:
 image=Bitmap(32,16)
 for y in range(16):
  for x in range(32):image.SetPixel(x,y,Color.FromArgb(20+x*7,20+y*14,220 if (x//4+y//4)%2 else 30))
 source=os.path.join(folder,tag+'.png');image.Save(source);image.Dispose()
 assets=[api('material_import',asset=dict(name=tag+' Same label',widthMeters=.6,heightMeters=.3),files=dict(baseColor=source)) for _ in range(2)]
 li=layer('_objects');lli=layer('_bylayer');other=layer('_other')
 first=plane(0,0,1.8,1.2,0,li,'Plane A');second=plane(2.1,0,1.8,1.2,0,lli,'Plane B')
 third=plane(4.2,0,1.8,1.2,0,other,'Plane C')
 box=add('Box',Box(Plane(p(0,2,0),Vector3d.ZAxis),Interval(0,1.2*scale),Interval(0,1.2*scale),Interval(0,1.2*scale)).ToBrep(),li)
 cylinder=add('Cylinder',Cylinder(Circle(Plane(p(2.7,2.6,0),Vector3d.ZAxis),.6*scale),1.4*scale).ToBrep(True,True),li)
 sphere=add('Sphere',Sphere(p(4.8,2.6,.6),.6*scale).ToBrep(),li)
 api('material_apply',assetId=assets[0]['id'],objects=[first],mapping=dict(mode='plane',alignment='continuous',originMeters=[100,100,0]))
 api('material_apply',assetId=assets[0]['id'],layers=[str(doc.Layers[lli].Id)],mapping=dict(mode='plane',alignment='continuous',originMeters=[100,100,0]))
 api('material_apply',assetId=assets[1]['id'],objects=[third],mapping=dict(mode='plane',alignment='continuous',originMeters=[100,100,0]))
 for id,mode in [(box,'box'),(cylinder,'cylinder'),(sphere,'auto')]:api('material_apply',assetId=assets[0]['id'],objects=[id],mapping=dict(mode=mode))
 effective=[str(doc.Objects.FindId(System.Guid(id)).GetRenderMaterial(True).Id) for id in [first,second,third,box,cylinder,sphere]]
 assert effective[0]==effective[1]==effective[3]==effective[4]==effective[5] and effective[0]!=effective[2],effective
 report['effectiveMaterials']=effective
 for name,projection in [('Top',Rhino.Display.DefinedViewportProjection.Top),('Perspective',Rhino.Display.DefinedViewportProjection.Perspective)]:
  vp=Rhino.Display.RhinoViewport();vp.Size=System.Drawing.Size(384,256);vp.SetProjection(projection,name,True)
  if name=='Perspective':vp.SetCameraLocations(p(3,1.6,.5),p(10,-8,9))
  vp.ZoomBoundingBox(BoundingBox(p(-.1,-.1,-.1),p(6.1,3.4,1.5)))
  info=Rhino.DocObjects.ViewInfo(vp);info.Name=tag+'_'+name;index=doc.NamedViews.Add(info);views.append(doc.NamedViews[index].NamedViewId);info.Dispose();vp.Dispose()
 for view in views:
  row=next(v for v in api('workbench_settings')['views'] if v['id']==str(view))
  assert [l['kind'] for l in row['layers']]==['shadow','texture'] and row['layers'][0]['blend']=='mul '
  assert row['layers'][1]['textureGrouping']=='material'
 before=state()
 # Record native mapping basis and camera for an independent physical-scale pixel oracle.
 row=next(r for r in WorkbenchService.Settings(doc) if r.Id==views[0]);vp=Rhino.Display.RhinoViewport();vp.Size=System.Drawing.Size(384,256)
 WorkbenchService.ApplyCamera(doc,row,vp,384,256)
 def xyz(v):return [v.X,v.Y,v.Z]
 report['topCamera']=dict(origin=xyz(vp.CameraLocation),right=xyz(vp.CameraX),up=xyz(vp.CameraY),back=xyz(vp.CameraZ),frustum=list(vp.GetFrustum())[1:])
 o=doc.Objects.FindId(System.Guid(first));mapping=o.GetTextureMapping(1);native=o.GetRenderMaterial(True).ToMaterial(Rhino.Render.RenderTexture.TextureGeneration.Disallow);texture=native.GetBitmapTexture()
 uv=[]
 for pt in [p(0,0,0),p(1,0,0),p(0,1,0)]:
  _,q=mapping.Evaluate(pt,Vector3d.ZAxis);q.Transform(texture.UvwTransform);uv.append(xyz(q))
 report['uvBasis']=uv;report['planeOrigin']=xyz(p(0,0,0));report['unitsPerMeter']=scale;report['source']=source
 assert abs(uv[1][0]-uv[0][0]-1/.6)<1e-5 and abs(uv[2][1]-uv[0][1]-1/.3)<1e-5,uv
 texture.Dispose();native.Dispose();mapping.Dispose();vp.Dispose()
 for grouping in ['material','object']:
  for view in views:api('configure_view',viewId=str(view),settings=dict(width=384,height=256,layers=[dict(kind='texture',textureGrouping=grouping)]))
  result=api('export_workbench',directory=os.path.join(folder,tag+'_'+grouping),views=[str(v) for v in views]);assert all(f['ok'] for f in result['files']),result
  report['exports'][grouping]=result;assert state()==before,'Export changed Rhino state'
 # Sun changes cannot alter the unlit material pass.
 api('configure_view',viewId=str(views[0]),settings=dict(sun=dict(useDocument=False,azimuth=230,altitude=25)))
 report['exports']['sun']=api('export_workbench',directory=os.path.join(folder,tag+'_sun'),views=[str(views[0])]);assert state()==before
 api('configure_view',viewId=str(views[1]),settings=dict(layers=[dict(kind='shadow',blend='mul ',opacity=65),dict(kind='texture')]))
 report['exports']['shadow']=api('export_workbench',directory=os.path.join(folder,tag+'_shadow'),views=[str(views[1])]);assert all(f['ok'] for f in report['exports']['shadow']['files'])
 assert state()==before
 # Classic Rhino material without an RDK assignment: shared identity and diffuse fallback.
 legacy=Rhino.DocObjects.Material();legacy.Name=tag+' classic';legacy.DiffuseColor=Color.FromArgb(43,93,167);mi=doc.Materials.Add(legacy);legacy.Dispose()
 classicLayerDefinition=Rhino.DocObjects.Layer();classicLayerDefinition.Name=tag+'_classic';classicLayerDefinition.RenderMaterialIndex=mi
 classicLayer=doc.Layers.Add(classicLayerDefinition);layers.append(doc.Layers[classicLayer].Id);assert doc.Layers[classicLayer].RenderMaterialIndex==mi
 classic1=plane(20,0,1,1,0,classicLayer,'Classic object');classic2=plane(21.2,0,1,1,0,classicLayer,'Classic layer')
 for classicId in [classic1,classic2]:
  o=doc.Objects.FindId(System.Guid(classicId));a=o.Attributes.Duplicate();a.MaterialSource=Rhino.DocObjects.ObjectMaterialSource.MaterialFromObject;a.MaterialIndex=mi;assert doc.Objects.ModifyAttributes(o,a,True)
 vp=Rhino.Display.RhinoViewport();vp.Size=System.Drawing.Size(256,128);vp.SetProjection(Rhino.Display.DefinedViewportProjection.Top,'Top',True);vp.ZoomBoundingBox(BoundingBox(p(19.9,-.1,-.1),p(22.3,1.1,.1)))
 info=Rhino.DocObjects.ViewInfo(vp);info.Name=tag+'_Classic';vi=doc.NamedViews.Add(info);classicView=doc.NamedViews[vi].NamedViewId;views.append(classicView);info.Dispose();vp.Dispose()
 api('configure_view',viewId=str(classicView),settings=dict(width=256,height=128,layers=[dict(kind='texture')]))
 classicState=state();report['exports']['classic']=api('export_workbench',directory=os.path.join(folder,tag+'_classic'),views=[str(classicView)])
 assert all(f['ok'] for f in report['exports']['classic']['files']) and state()==classicState
 report['classicRenderMaterialMissing']=doc.Objects.FindId(System.Guid(classic1)).GetRenderMaterial(True) is None
 report['classicEffectiveIndices']=[doc.Objects.FindId(System.Guid(id)).Attributes.MaterialIndex for id in [classic1,classic2]]
 doc.Objects.Delete(System.Guid(classic1),True);doc.Objects.Delete(System.Guid(classic2),True)
 # Configuration copies must retain grouping without sharing mutable layer settings.
 sourceRow=next(r for r in WorkbenchService.Settings(doc) if r.Id==views[1]);copy=sourceRow.Copy()
 assert copy.Layers[1].TextureGrouping=='material';copy.Layers[1].TextureGrouping='object'
 assert sourceRow.Layers[1].TextureGrouping=='material';report['configurationCopyIndependent']=True
 bad=raw('configure_view',viewId=str(views[0]),settings=dict(layers=[dict(kind='texture',textureGrouping='name')]))
 assert not bad['ok'];report['invalidGroupingRejected']=True
 # A new object inheriting a SceneFlow layer material has no calibrated mapping yet.
 new=plane(0,0,.2,.2,-2,lli,'New layer object without UV');newState=state()
 api('configure_view',viewId=str(views[0]),settings=dict(layers=[dict(kind='texture')]))
 bad=api('export_workbench',directory=os.path.join(folder,tag+'_new-layer'),views=[str(views[0])]);assert not bad['files'][0]['ok'],bad
 assert state()==newState;doc.Objects.Delete(System.Guid(new),True);report['newLayerUvReadOnlyRejected']=True
 # Missing bitmaps and transparency must fail, rather than become a flat or opaque substitute.
 missing=os.path.join(api('material_library')['directory'],'assets',assets[0]['id'].replace('-',''),assets[0]['maps']['baseColor']);parked=missing+'.test-missing'
 os.rename(missing,parked)
 try:
  current=state();bad=api('export_workbench',directory=os.path.join(folder,tag+'_missing'),views=[str(views[0])]);assert not bad['files'][0]['ok'],bad
  assert state()==current;report['missingBitmapReadOnlyRejected']=True
 finally:os.rename(parked,missing)
 alpha=Bitmap(source);alpha.SetPixel(0,0,Color.FromArgb(0,255,0,0));alphaPath=os.path.join(folder,tag+'_alpha.png');alpha.Save(alphaPath);alpha.Dispose()
 alphaAsset=api('material_import',asset=dict(name=tag+' alpha',widthMeters=.6,heightMeters=.3),files=dict(baseColor=alphaPath))
 api('material_apply',assetId=alphaAsset['id'],objects=[first]);current=state()
 bad=api('export_workbench',directory=os.path.join(folder,tag+'_alpha'),views=[str(views[0])]);assert not bad['files'][0]['ok'],bad
 assert state()==current;report['alphaBitmapReadOnlyRejected']=True
 api('material_apply',assetId=assets[0]['id'],objects=[first])
 # A stale real-world mapping rejects read-only export and must not silently repair the object.
 o=doc.Objects.FindId(System.Guid(first));a=o.Attributes.Duplicate();a.SetUserString('RhinoSceneFlow.WorldUv',None);assert doc.Objects.ModifyAttributes(o,a,True)
 api('configure_view',viewId=str(views[0]),settings=dict(layers=[dict(kind='texture')]))
 stale=state();bad=api('export_workbench',directory=os.path.join(folder,tag+'_stale'),views=[str(views[0])]);assert not bad['files'][0]['ok'],bad
 assert state()==stale;report['staleUvReadOnlyRejected']=True
 report['stateUnchanged']=True;report['complete']=True
finally:
 for id in ids:
  o=doc.Objects.FindId(id)
  if o is not None and o.Attributes.GetUserString('SceneFlow.TextureTest')==tag:doc.Objects.Delete(id,True)
 for i in range(doc.NamedViews.Count-1,-1,-1):
  if doc.NamedViews[i].NamedViewId in views:doc.NamedViews.Delete(i)
 for id in reversed(layers):
  l=doc.Layers.FindId(id)
  if l is not None:doc.Layers.Delete(l.Index,True)
 doc.Modified=originalModified;doc.Views.RedrawEnabled=originalRedraw;doc.Views.Redraw()
 with open(os.path.join(folder,'report.json'),'w') as f:json.dump(report,f,indent=2)
print(json.dumps(report))

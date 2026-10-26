"""Real B-only physical mappings, material inheritance/restoration and Agent job handoff.
Creates and removes only uniquely tagged test geometry; never clears the current model.
"""
import Rhino,System,clr,json,os,math
from System.Reflection import BindingFlags
from System.Drawing import Bitmap,Graphics,Color,Brushes
from Rhino.Geometry import Point3d,Vector3d,Plane,Interval,Box,Circle,Cylinder,Brep,Transform
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi,MaterialService,MaterialPanelController
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;stamp=str(System.Guid.NewGuid())[:8]
folder=os.path.join(OUTPUT_DIR,'materials','run-'+stamp);os.makedirs(folder,exist_ok=True)
original_modified=doc.Modified;original_selection=[o.Id for o in doc.Objects.GetSelectedObjects(False,False)]
original_ids=sorted(str(o.Id) for o in doc.Objects);created=[];layers=[];material_ids=[]
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
def field(obj,key):return obj.GetType().GetField(key,BindingFlags.Instance|BindingFlags.NonPublic).GetValue(obj)
def walk(obj):
 yield obj
 if hasattr(obj,'Controls'):
  for c in obj.Controls:
   for child in walk(c):yield child
def click(text):
 b=next(c for c in walk(panel.Content) if c.GetType().Name=='Button' and c.Text==text)
 b.GetType().GetMethod('PerformClick').Invoke(b,None)
def add_layer(suffix):
 l=Rhino.DocObjects.Layer();l.Name='SF_MaterialTest_'+stamp+'_'+suffix;index=doc.Layers.Add(l);layers.append(index);return index
def add(geometry,layer_index):
 a=Rhino.DocObjects.ObjectAttributes();a.LayerIndex=layer_index;a.SetUserString('SceneFlow.MaterialTest',stamp);id=doc.Objects.Add(geometry,a);assert id!=System.Guid.Empty;created.append(id);return id
def uv(id,p,n):
 mapping=doc.Objects.FindId(id).GetTextureMapping(1);assert mapping is not None
 try:
  side,t=mapping.Evaluate(p,n);assert side!=0
  binding=doc.Objects.FindId(id).Attributes.GetUserString('RhinoSceneFlow.Material')
  if binding:
   a=api('material_library')['assets'];asset_id=json.loads(binding)['asset'];current=next(v for v in a if v['id']==asset_id)
   return [t.X/current['widthMeters'],t.Y/current['heightMeters']]
  return [t.X,t.Y]
 finally:mapping.Dispose()
def close(a,b,tol=1e-5):assert abs(a-b)<tol,(a,b)
def delta(id,a,b,n):return [y-x for x,y in zip(uv(id,a,n),uv(id,b,n))]
def apply(id,mode,**kw):
 api('material_prepare_uv',objects=[str(id)],mapping=dict(mode=mode,**kw),force=True)
 return api('material_apply',assetId=asset['id'],objects=[str(id)],mapping=dict(mode=mode,**kw))
original_library=api('material_library')['directory'];report=dict(pid=EXPECTED_PID,folder=folder)
try:
 api('material_configure',directory=os.path.join(folder,'library'))
 path=os.path.join(folder,'grid.png');bitmap=Bitmap(256,128);g=Graphics.FromImage(bitmap);g.Clear(Color.White);g.FillRectangle(Brushes.DarkGray,0,0,128,64);g.FillRectangle(Brushes.DarkGray,128,64,128,64);bitmap.Save(path);g.Dispose();bitmap.Dispose()
 files=dict(baseColor=path)
 for slot,color in [('roughness',Color.FromArgb(166,166,166)),('metallic',Color.Black),('normal',Color.FromArgb(128,128,255))]:
  f=os.path.join(folder,slot+'.png');b=Bitmap(64,64);gg=Graphics.FromImage(b);gg.Clear(color);b.Save(f);gg.Dispose();b.Dispose();files[slot]=f
 asset=api('material_import',asset=dict(name='600x300 mm calibration',widthMeters=.6,heightMeters=.3),files=files);material_ids.append(asset['id'])
 scale=MaterialService.UnitScale(doc);w=.6*scale;h=.3*scale
 index=add_layer('objects')
 plane_id=add(Brep.CreateFromCornerPoints(Point3d(0,0,0),Point3d(4*w,0,0),Point3d(4*w,4*h,0),Point3d(0,4*h,0),doc.ModelAbsoluteTolerance),index)
 old_material=Rhino.DocObjects.Material();old_material.DiffuseColor=Color.Red
 old_render=Rhino.Render.RenderMaterial.FromMaterial(old_material,doc);doc.RenderMaterials.Add(old_render);old_render_id=old_render.Id
 old_obj=doc.Objects.FindId(plane_id);old_obj.RenderMaterial=old_render;old_obj.CommitChanges();old_attrs=old_obj.Attributes.Duplicate();old_attrs.MaterialSource=Rhino.DocObjects.ObjectMaterialSource.MaterialFromObject;doc.Objects.ModifyAttributes(plane_id,old_attrs,True);old_material.Dispose()
 previous=Rhino.Render.TextureMapping.CreatePlaneMapping(Plane.WorldXY,Interval(0,2*w),Interval(0,2*h),Interval(-1,1));doc.Objects.FindId(plane_id).SetTextureMapping(1,previous);previous.Dispose()
 old_uv=uv(plane_id,Point3d(w,h,0),Vector3d.ZAxis)
 preview=api('material_preview',assetId=asset['id'],objects=[str(plane_id)],mapping=dict(mode='plane'))
 assert doc.Objects.FindId(plane_id).Attributes.GetUserString('RhinoSceneFlow.Material') is None
 apply(plane_id,'plane');d=delta(plane_id,Point3d(.1*w,.1*h,0),Point3d(1.1*w,1.1*h,0),Vector3d.ZAxis);close(d[0],1);close(d[1],1)
 obj=doc.Objects.FindId(plane_id);assert obj.RenderMaterial is not None
 simulated=obj.RenderMaterial.SimulatedMaterial(Rhino.Render.RenderTexture.TextureGeneration.Allow)
 report['pbr']=dict(isPbr=simulated.IsPhysicallyBased,textures=[str(t.TextureType) for t in simulated.GetTextures()])
 assert simulated.IsPhysicallyBased
 close(simulated.PhysicallyBased.Roughness,.65)
 report['pbr']['baseColorChannel']=simulated.GetBitmapTexture().MappingChannelId
 normal_texture=obj.RenderMaterial.GetTextureFromUsage(Rhino.Render.RenderMaterial.StandardChildSlots.Bump)
 report['pbr']['normalRecognized']=normal_texture.IsNormalMap() if normal_texture is not None else None
 if normal_texture is not None:
  with open(os.path.join(folder,'normal-render.xml'),'w',encoding='utf-8') as f:f.write(str(normal_texture.Xml))
 report['planeRepeat']=d
 apply(plane_id,'plane',rotation=90);d=delta(plane_id,Point3d(.1*w,.1*h,0),Point3d(1.1*w,.1*h,0),Vector3d.ZAxis);close(d[0],0);close(d[1],-2)
 a=doc.Objects.FindId(plane_id).Attributes.Duplicate();a.Name='Keep this later edit';doc.Objects.ModifyAttributes(plane_id,a,True)
 api('material_restore',objects=[str(plane_id)]);assert doc.Objects.FindId(plane_id).Attributes.Name=='Keep this later edit';assert doc.Objects.FindId(plane_id).RenderMaterial.Id==old_render_id;now=uv(plane_id,Point3d(w,h,0),Vector3d.ZAxis);close(now[0],old_uv[0]);close(now[1],old_uv[1]);report['restoration']=True
 box_id=add(Box(Plane.WorldXY,Interval(0,4*w),Interval(0,4*h),Interval(0,4*h)).ToBrep(),index)
 apply(box_id,'box')
 for normal,a,b in [(Vector3d.ZAxis,Point3d(.1*w,.1*h,4*h),Point3d(1.1*w,1.1*h,4*h)),(Vector3d(0,-1,0),Point3d(.1*w,0,.1*h),Point3d(1.1*w,0,1.1*h)),(Vector3d.XAxis,Point3d(4*w,.1*w,.1*h),Point3d(4*w,1.1*w,1.1*h))]:
  d=delta(box_id,a,b,normal);close(d[0],1);close(d[1],1)
 report['rectangularBox']=True
 radius=.5*scale;cp=Plane(Point3d(6*w,0,0),Vector3d.ZAxis);cyl_id=add(Cylinder(Circle(cp,radius),3*scale).ToBrep(False,False),index)
 apply(cyl_id,'cylinder');center=cp.Origin
 d=delta(cyl_id,Point3d(center.X+radius,center.Y,.1*scale),Point3d(center.X,center.Y+radius,.4*scale),Vector3d.XAxis)
 close(d[0],math.pi*radius/2/w);close(d[1],1);report['cylinderRepeat']=d
 layer_index=add_layer('layer');layer_id=doc.Layers[layer_index].Id
 layer_obj=add(Brep.CreateFromCornerPoints(Point3d(0,5*h,0),Point3d(2*w,5*h,0),Point3d(2*w,7*h,0),Point3d(0,7*h,0),doc.ModelAbsoluteTolerance),layer_index)
 api('material_apply',assetId=asset['id'],layers=[str(layer_id)],mapping=dict(mode='plane'))
 assert doc.Objects.FindId(layer_obj).Attributes.MaterialSource==Rhino.DocObjects.ObjectMaterialSource.MaterialFromLayer
 assert doc.Layers[layer_index].RenderMaterial is not None
 api('material_remap',objects=[str(layer_obj)]);assert doc.Objects.FindId(layer_obj).Attributes.MaterialSource==Rhino.DocObjects.ObjectMaterialSource.MaterialFromLayer
 new_layer_obj=add(Brep.CreateFromCornerPoints(Point3d(3*w,5*h,0),Point3d(4*w,5*h,0),Point3d(4*w,7*h,0),Point3d(3*w,7*h,0),doc.ModelAbsoluteTolerance),layer_index)
 api('material_remap',layers=[str(layer_id)]);assert doc.Objects.FindId(new_layer_obj).GetTextureMapping(1) is not None;report['newLayerObjectSync']=True
 api('material_restore',layers=[str(layer_id)]);assert doc.Layers[layer_index].RenderMaterial is None;report['layerInheritanceAndRestore']=True
 apply(plane_id,'plane');doc.Objects.Transform(plane_id,Transform.Scale(Point3d.Origin,2),True)
 assert api('material_inspect',objects=[str(plane_id)])[0]['needsRemap'];api('material_remap',objects=[str(plane_id)]);assert not api('material_inspect',objects=[str(plane_id)])[0]['needsRemap'];report['scaledObjectRemap']=True
 for unit,expected in [(Rhino.UnitSystem.Millimeters,1000),(Rhino.UnitSystem.Meters,1),(Rhino.UnitSystem.Feet,1/.3048),(Rhino.UnitSystem.Inches,1/.0254)]:
  hd=Rhino.RhinoDoc.CreateHeadless(None)
  try:hd.ModelUnitSystem=unit;close(MaterialService.UnitScale(hd),expected)
  finally:hd.Dispose()
 report['unitConversion']=True
 mesh=Rhino.Geometry.Mesh()
 for xyz,tex in [((0,0,5*scale),(.2,.1)),((w,0,5*scale),(.8,.1)),((w,h,5*scale),(.8,.9)),((0,h,5*scale),(.2,.9))]:mesh.Vertices.Add(*xyz);mesh.TextureCoordinates.Add(*tex)
 mesh.Faces.AddFace(0,1,2,3);mesh.Normals.ComputeNormals();mesh_id=add(mesh,index)
 old_mesh_uv=[(t.X,t.Y) for t in doc.Objects.FindId(mesh_id).Geometry.TextureCoordinates]
 apply(mesh_id,'box');api('material_restore',objects=[str(mesh_id)]);assert old_mesh_uv==[(t.X,t.Y) for t in doc.Objects.FindId(mesh_id).Geometry.TextureCoordinates];report['originalMeshUvPreserved']=True
 package=os.path.join(folder,'calibration.zip');api('material_pack',assetId=asset['id'],path=package);unpacked=api('material_unpack',path=package);close(unpacked['widthMeters'],.6);report['package']=True
 api('material_open_panel');panel=MaterialPanelController.Find(doc.RuntimeSerialNumber);panel.Select(System.Guid(asset['id']))
 doc.Objects.UnselectAll();doc.Objects.FindId(plane_id).Select(True);click('应用材质');assert doc.Objects.FindId(plane_id).Attributes.GetUserString('RhinoSceneFlow.Material') is not None
 field(panel,'name').Text='AI Limestone 1 m';field(panel,'prompt').Text='浅暖灰石灰岩，均匀中性光，无接缝，完整贴图代表 1×1 米。';field(panel,'width').Value=1000;field(panel,'height').Value=1000;click('请求 Agent 生成')
 state=api('material_panel_status');job=state['lastJob'];assert next(j for j in api('material_generation_jobs') if j['id']==job)['status']=='pending'
 ai_path=os.path.join(os.path.dirname(OUTPUT_DIR),'materials','source','ai-limestone-basecolor.png')
 ai=api('material_generation_complete',jobId=job,files=dict(baseColor=ai_path));assert ai['source']=='ai-agent' and ai['widthMeters']==1
 panel.GetType().GetMethod('PollGeneration',BindingFlags.Instance|BindingFlags.NonPublic).Invoke(panel,None)
 assert api('material_panel_status')['selected']==ai['id'];report['agentGeneratedAsset']=ai;report['uiApplyAndJob']=True
 # Regression: Rhino's material simulation may resolve identical basenames from
 # different folders to the last bitmap. Asset-prefixed map names must isolate them.
 api('material_apply',assetId=ai['id'],objects=[str(plane_id)],mapping=dict(mode='plane'))
 library=api('material_library')['directory']
 for id,spec in [(box_id,asset),(plane_id,ai),(box_id,asset)]:
  simulated=doc.Objects.FindId(id).GetRenderMaterial(True).SimulatedMaterial(Rhino.Render.RenderTexture.TextureGeneration.Allow)
  expected=os.path.join(library,'assets',spec['id'].replace('-',''),spec['maps']['baseColor'])
  assert os.path.normcase(simulated.GetBitmapTexture().FileName)==os.path.normcase(expected),(simulated.GetBitmapTexture().FileName,expected)
 report['multipleAssetTextureIsolation']=True
 report['complete']=True
finally:
 panel=MaterialPanelController.Find(doc.RuntimeSerialNumber)
 if panel is not None:panel.Close()
 for id in created:
  obj=doc.Objects.FindId(id)
  if obj is not None and obj.Attributes.GetUserString('SceneFlow.MaterialTest')==stamp:doc.Objects.Delete(id,True)
 for index in reversed(layers):
  if not doc.Objects.FindByLayer(doc.Layers[index]):doc.Layers.Delete(index,True)
 doc.Objects.UnselectAll()
 for id in original_selection:
  obj=doc.Objects.FindId(id)
  if obj is not None:obj.Select(True)
 api('material_configure',directory=original_library);doc.Modified=original_modified
 report['geometryCountRestored']=sorted(str(o.Id) for o in doc.Objects)==original_ids
 with open(os.path.join(folder,'report.json'),'w',encoding='utf-8') as f:json.dump(report,f,indent=2)
 with open(os.path.join(OUTPUT_DIR,'materials','latest.json'),'w') as f:json.dump(dict(folder=folder,pid=EXPECTED_PID,complete=report.get('complete',False)),f)
print(json.dumps(report))

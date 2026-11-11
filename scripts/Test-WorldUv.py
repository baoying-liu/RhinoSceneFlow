"""B native SDK regression: independent meter UV, material scaling and cache invalidation."""
import Rhino,System,clr,json,os
from Rhino.Geometry import Point3d,Vector3d,Transform,Brep,Plane,Interval
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import MaterialService
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
D=__rhino_doc__;stamp=str(System.Guid.NewGuid())[:8]
folder=os.path.join(OUTPUT_DIR,'worlduv',stamp);os.makedirs(folder,exist_ok=True)
created=[];layers=[];old_modified=D.Modified;old_ids=set(str(o.Id) for o in D.Objects)
selected=[o.Id for o in D.Objects.GetSelectedObjects(False,False)]
report=dict(pid=EXPECTED_PID,folder=folder)
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(D.RuntimeSerialNumber),**kw))));assert r['ok'],r
 return r['result']
def valid(id):return api('material_uv_status',objects=[str(id)])[0]['status']['valid']
def obj(id):return D.Objects.FindId(id)
def add(index,x=0):
 a=Rhino.DocObjects.ObjectAttributes();a.LayerIndex=index;a.SetUserString('SceneFlow.WorldUvTest',stamp)
 s=MaterialService.UnitScale(D)
 id=D.Objects.AddBrep(Brep.CreateFromCornerPoints(Point3d(x,0,0),Point3d(x+2*s,0,0),Point3d(x+2*s,2*s,0),Point3d(x,2*s,0),.001),a);created.append(id);return id
def delta(id):
 s=MaterialService.UnitScale(D);m=obj(id).GetTextureMapping(1)
 try:
  _,a=m.Evaluate(Point3d(0,0,0),Vector3d.ZAxis);_,b=m.Evaluate(Point3d(s,s,0),Vector3d.ZAxis)
  return [b.X-a.X,b.Y-a.Y]
 finally:m.Dispose()
def close(a,b):assert abs(a-b)<1e-5,(a,b)
try:
 layer=Rhino.DocObjects.Layer();layer.Name='WorldUV-'+stamp;index=D.Layers.Add(layer);layers.append(D.Layers[index].Id)
 id=add(index);s=MaterialService.UnitScale(D)
 assets=api('material_library')['assets'];assert assets,'Prepare material demo first'
 asset=next(a for a in assets if a['widthMeters']!=a['heightMeters'])
 material_before=(obj(id).Attributes.MaterialSource,obj(id).Attributes.MaterialIndex)
 r=api('material_prepare_uv',objects=[str(id)]);assert r['computed']==1 and valid(id),r
 assert material_before==(obj(id).Attributes.MaterialSource,obj(id).Attributes.MaterialIndex)
 close(delta(id)[0],1);close(delta(id)[1],1);report['standaloneMetersAndMaterialPreserved']=True
 record=obj(id).Attributes.GetUserString('RhinoSceneFlow.WorldUv')
 r=api('material_apply',assetId=asset['id'],objects=[str(id)]);assert r['uvComputed']==0 and r['uvReused']==1,r
 assert obj(id).Attributes.GetUserString('RhinoSceneFlow.WorldUv')==record
 simulated=obj(id).RenderMaterial.SimulatedMaterial(Rhino.Render.RenderTexture.TextureGeneration.Allow)
 tex=simulated.GetBitmapTexture();point=Point3d(1,1,0);point.Transform(tex.UvwTransform)
 # Since v0.14 structured/stochastic/macro bakes contain Tiles base periods.
 # Their RDK repeat is for the supertile; WorldUv itself is still one unit/meter.
 random=MaterialService.Library.Get(System.Guid(asset['id'])).Randomization
 span=1 if random.ResolvedMode in ('off','object') else random.Tiles
 close(point.X,1/(asset['widthMeters']*span));close(point.Y,1/(asset['heightMeters']*span));report['textureScale']=[point.X,point.Y];report['bakedPeriods']=span
 other=next(a for a in assets if a['id']!=asset['id'])
 r=api('material_apply',assetId=other['id'],objects=[str(id)]);assert r['uvComputed']==0 and r['uvReused']==1
 assert obj(id).Attributes.GetUserString('RhinoSceneFlow.WorldUv')==record;report['materialSwitchReusesUv']=True
 # Editing an existing channel invalidates the stored provenance.
 m=Rhino.Render.TextureMapping.CreatePlaneMapping(Plane.WorldXY,Interval(0,2*s),Interval(0,2*s),Interval(-1,1));obj(id).SetTextureMapping(1,m);m.Dispose()
 assert not valid(id)
 r=api('material_apply',assetId=asset['id'],objects=[str(id)]);assert r['uvComputed']==1 and valid(id);report['externalMappingEditDetected']=True
 # Same bounds, different internal geometry must invalidate (bbox-only checks miss this).
 mesh=Rhino.Geometry.Mesh();mesh.Vertices.Add(0,0,0);mesh.Vertices.Add(s,0,0);mesh.Vertices.Add(s,s,0);mesh.Vertices.Add(0,s,0);mesh.Vertices.Add(.5*s,.5*s,0)
 for a,b in [(0,1),(1,2),(2,3),(3,0)]:mesh.Faces.AddFace(a,b,4)
 a=Rhino.DocObjects.ObjectAttributes();a.LayerIndex=index;a.SetUserString('SceneFlow.WorldUvTest',stamp);mid=D.Objects.AddMesh(mesh,a);created.append(mid);mesh.Dispose()
 api('material_prepare_uv',objects=[str(mid)]);assert valid(mid)
 changed=obj(mid).Geometry.DuplicateMesh();changed.Vertices.SetVertex(4,.4*s,.5*s,0);D.Objects.Replace(mid,changed);changed.Dispose();assert not valid(mid);report['internalGeometryEditDetected']=True
 D.Objects.Transform(id,Transform.Scale(Point3d.Origin,2),True);assert not valid(id)
 r=api('material_apply',assetId=asset['id'],objects=[str(id)]);assert r['uvComputed']==1 and valid(id);report['transformDetected']=True
 # Units invalidate even when geometry coordinates have not changed.
 units=D.ModelUnitSystem
 try:D.ModelUnitSystem=Rhino.UnitSystem.Meters if units!=Rhino.UnitSystem.Meters else Rhino.UnitSystem.Millimeters;assert not valid(id)
 finally:D.ModelUnitSystem=units
 api('material_restore',objects=[str(id)]);assert obj(id).Attributes.GetUserString('RhinoSceneFlow.WorldUv') is None and obj(id).GetTextureMapping(1) is None;report['restoreOriginalNoUv']=True
 api('material_prepare_uv',objects=[str(id)]);newid=add(index,3*s)
 # Invalid mesh is still in the layer and should also be recalculated.
 r=api('material_apply',assetId=asset['id'],layers=[str(D.Layers[index].Id)]);assert r['uvComputed']==2 and r['uvReused']==1,r
 assert all(valid(i) for i in created);report['mixedLayerMissingInvalidAndValid']=True
 # Real reference attachment and truthful progress through native API.
 source=MaterialService.Library.MapPath(MaterialService.Library.Get(System.Guid(asset['id'])),'baseColor')
 job=api('material_generation_request',asset=dict(name='Reference test',widthMeters=1,heightMeters=1),prompt='Reference limestone',referenceImages=[source])
 assert len(job['referenceImages'])==1 and os.path.isfile(job['referenceImages'][0])
 update=api('material_generation_progress',jobId=job['id'],stage='Generating image');assert update['status']=='running'
 api('material_generation_cancel',jobId=job['id']);report['referenceAndProgress']=True
 report['complete']=True
finally:
 for id in created:
  if obj(id) is not None and obj(id).Attributes.GetUserString('SceneFlow.WorldUvTest')==stamp:D.Objects.Delete(id,True)
 for id in layers:D.Layers.Delete(D.Layers.FindId(id).Index,True)
 D.Objects.UnselectAll()
 for id in selected:
  if obj(id) is not None:obj(id).Select(True)
 D.Modified=old_modified;D.Views.Redraw();report['liveIdsRestored']=old_ids==set(str(o.Id) for o in D.Objects)
 with open(os.path.join(folder,'report.json'),'w') as f:json.dump(report,f,indent=2)
 with open(os.path.join(OUTPUT_DIR,'worlduv','latest.json'),'w') as f:json.dump(dict(folder=folder,complete=report.get('complete',False)),f)
print(json.dumps(report))

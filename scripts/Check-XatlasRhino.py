import Rhino,System,clr,json,os,time
from Rhino.Geometry import BoundingBox,Point3d
from System.Drawing import Bitmap,Color
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi,MaterialQuickController
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'xatlas');s=json.load(open(os.path.join(folder,'start.json')));assert s['pid']==EXPECTED_PID
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))));assert r['ok'],r;return r['result']
j=api('material_unwrap_status',jobId=s['job']['id']);assert j['status']=='completed',j
for source in s['objects']:
 o=doc.Objects.FindId(System.Guid(source['id']));assert int(o.Geometry.DataCRC(0))==source['crc'] and o.Geometry.GetType().Name==source['type']
 withmap=o.GetTextureMapping(1);ok,mesh=withmap.TryGetMappingMesh();assert ok and mesh.IsValid and mesh.TextureCoordinates.Count==mesh.Vertices.Count
 assert all(not System.Single.IsNaN(v.X) and not System.Single.IsNaN(v.Y) for v in mesh.TextureCoordinates)
 source['mappingVertices']=mesh.Vertices.Count;source['mappingTriangles']=mesh.Faces.Count
 mesh.Dispose();withmap.Dispose()
 assert api('material_uv_status',objects=[source['id']])[0]['status']['valid']
ids=[o['id'] for o in s['objects']];image=Bitmap(128,128)
for y in range(128):
 for x in range(128):image.SetPixel(x,y,Color.FromArgb(230,230,220) if (x//16+y//16)%2 else Color.FromArgb(45,100,170))
path=os.path.join(folder,'checker.png');image.Save(path);image.Dispose()
asset=api('material_import',asset=dict(name='xatlas 1m checker',widthMeters=1,heightMeters=1),files=dict(baseColor=path));api('material_apply',assetId=asset['id'],objects=ids)
for source in s['objects']:
 o=doc.Objects.FindId(System.Guid(source['id']));assert int(o.Geometry.DataCRC(0))==source['crc'];assert api('material_uv_status',objects=[source['id']])[0]['status']['record']['mode']=='xatlas'
scale=s['unitsPerMeter'];vp=Rhino.Display.RhinoViewport();vp.Size=System.Drawing.Size(1024,768);vp.SetProjection(Rhino.Display.DefinedViewportProjection.Perspective,'Xatlas',True)
vp.SetCameraLocations(Point3d(100*scale,100*scale,4*scale),Point3d(123*scale,70*scale,26*scale));vp.ZoomBoundingBox(BoundingBox(Point3d(90*scale,90*scale,0),Point3d(115*scale,110*scale,9*scale)))
info=Rhino.DocObjects.ViewInfo(vp);info.Name=s['tag'];vi=doc.NamedViews.Add(info);view=str(doc.NamedViews[vi].NamedViewId);info.Dispose();vp.Dispose()
api('configure_view',viewId=view,settings=dict(width=1024,height=768,layers=[dict(kind='texture',textureGrouping='object')]))
export=api('export_workbench',directory=folder,views=[view]);assert all(f['ok'] for f in export['files']),export
# Write the exact native document to a new test-only path; never overwrite a user file.
model=os.path.join(folder,s['tag']+'.3dm');assert doc.WriteFile(model,Rhino.FileIO.FileWriteOptions())
stored=Rhino.FileIO.File3dm.Read(model);assert stored is not None
for source in s['objects']:
 item=next(o for o in stored.Objects if str(o.Attributes.ObjectId)==source['id']);assert int(item.Geometry.DataCRC(0))==source['crc']
 mapping,transform=item.GetTextureMapping(1);assert mapping is not None
 ok,mapped=mapping.TryGetMappingMesh();assert ok and mapped.IsValid and mapped.TextureCoordinates.Count==source['mappingVertices'];mapped.Dispose();mapping.Dispose()
 source['mappingPersisted']=True
stored.Dispose()
api('material_quick_open',objects=[ids[0]])
p=MaterialQuickController.Find(doc.RuntimeSerialNumber);p.SelectAsset(System.Guid(asset['id']))
s.update(result=j,exports=export,asset=asset['id'],view=view,model=model,completed=time.time())
with open(os.path.join(folder,'verified.json'),'w') as f:json.dump(s,f,indent=2)
print(json.dumps(dict(uv=j,export=export,model=model,panel=api('material_quick_status'))))

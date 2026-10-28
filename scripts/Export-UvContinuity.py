"""Export isolated native / PSD brick comparisons, then persist the test document."""
import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'uv-v012');s=json.load(open(os.path.join(folder,'ready.json')))
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))));assert r['ok'],r;return r['result']
arctic=str(next(d for d in Rhino.Display.DisplayModeDescription.GetDisplayModes() if d.EnglishName=='Arctic').Id);rendered=str(Rhino.Display.DisplayModeDescription.RenderedId)
exports={};original={id:doc.Objects.FindId(System.Guid(id)).IsHidden for id in s['ids']}
try:
 for label,view,index in [('atlas',s['views'][0],0),('tube',s['views'][1],1)]:
  for i,id in enumerate(s['ids']):
   if i==index:doc.Objects.Show(System.Guid(id),True)
   else:doc.Objects.Hide(System.Guid(id),True)
  api('configure_view',viewId=view,settings=dict(width=1600,height=1200,layers=[dict(kind='texture')]))
  color=api('export_workbench',directory=os.path.join(folder,label,'albedo'),views=[view]);assert all(f['ok'] for f in color['files']),color
  api('configure_view',viewId=view,settings=dict(layers=[dict(kind='display',mode=rendered)]))
  native=api('export_workbench',directory=os.path.join(folder,label,'rendered'),views=[view]);assert all(f['ok'] for f in native['files']),native
  api('configure_view',viewId=view,settings=dict(layers=[dict(kind='shadow',blend='mul ',opacity=75),dict(kind='texture'),dict(kind='display',mode=arctic)]))
  stack=api('export_workbench',directory=os.path.join(folder,label,'stack'),views=[view]);assert all(f['ok'] for f in stack['files']),stack
  exports[label]=dict(albedo=color,rendered=native,stack=stack)
finally:
 for id,hidden in original.items():
  if hidden:doc.Objects.Hide(System.Guid(id),True)
  else:doc.Objects.Show(System.Guid(id),True)
for id,crc in zip(s['ids'],s['crc']):assert int(doc.Objects.FindId(System.Guid(id)).Geometry.DataCRC(0))==crc
model=os.path.join(folder,'UV-Continuity-Brick.3dm');assert doc.WriteFile(model,Rhino.FileIO.FileWriteOptions())
stored=Rhino.FileIO.File3dm.Read(model)
for id in s['ids']:
 item=next(o for o in stored.Objects if str(o.Attributes.ObjectId)==id);record=json.loads(item.Attributes.GetUserString('RhinoSceneFlow.WorldUv'))
 surface,xf=item.GetTextureMapping(1);assert surface.MappingType==Rhino.Render.TextureMappingType.SurfaceParameters;surface.Dispose()
 mapping,xf=item.GetTextureMapping(record['meshChannel']);ok,mesh=mapping.TryGetMappingMesh();assert ok and mesh.IsValid
 volume=Rhino.Geometry.VolumeMassProperties.Compute(mesh);assert volume and volume.Volume>0;volume.Dispose();mesh.Dispose();mapping.Dispose()
stored.Dispose();s.update(exports=exports,model=model,geometryUnchanged=True,persisted=True)
with open(os.path.join(folder,'export-verified.json'),'w') as f:json.dump(s,f,indent=2)
print(json.dumps(dict(exports=exports,model=model,renderer=api('material_uv_renderer'))))

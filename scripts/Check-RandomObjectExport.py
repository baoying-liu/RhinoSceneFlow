import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi,WorkbenchService
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'random014');setup=json.load(open(os.path.join(folder,'setup.json')))
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
assert not api('material_quick_status')['busy'],api('material_quick_status')
native=[]
for oid in setup['objects']:
 obj=doc.Objects.FindId(System.Guid(oid));render=obj.GetRenderMaterial(True);assert render is not None
 material=render.ToMaterial(Rhino.Render.RenderTexture.TextureGeneration.Disallow);texture=material.GetBitmapTexture();mapping=obj.GetTextureMapping(1)
 _,a=mapping.Evaluate(Rhino.Geometry.Point3d(0,0,0),Rhino.Geometry.Vector3d.ZAxis);_,b=mapping.Evaluate(Rhino.Geometry.Point3d(1000,0,0),Rhino.Geometry.Vector3d.ZAxis);a.Transform(texture.UvwTransform);b.Transform(texture.UvwTransform)
 assert abs(b.X-a.X-1)<1e-6,(a,b)
 _,c=mapping.Evaluate(Rhino.Geometry.Point3d(0,1000,0),Rhino.Geometry.Vector3d.ZAxis);c.Transform(texture.UvwTransform)
 bitmap=System.Drawing.Bitmap(texture.FileName);imageWidth=bitmap.Width;bitmap.Dispose()
 native.append(dict(id=str(render.Id),path=texture.FileName,width=imageWidth,repeatDelta=b.X-a.X,uvBasis=[[p.X,p.Y] for p in [a,b,c]]));texture.Dispose();material.Dispose();mapping.Dispose()
assert native[0]['id']!=native[1]['id'] and native[0]['path']!=native[1]['path'],native
before=(doc.Modified,[str(o.Id) for o in doc.Objects.GetSelectedObjects(False,False)],str(doc.Views.ActiveView.ActiveViewport.CameraLocation))
exports={}
for grouping in ['material','object']:
 api('configure_view',viewId=setup['view'],settings=dict(width=480,height=240,layers=[dict(kind='texture',textureGrouping=grouping)]))
 result=api('export_workbench',directory=os.path.join(folder,'objects-'+grouping),views=[setup['view']]);assert all(f['ok'] for f in result['files']),result;exports[grouping]=result
assert before==(doc.Modified,[str(o.Id) for o in doc.Objects.GetSelectedObjects(False,False)],str(doc.Views.ActiveView.ActiveViewport.CameraLocation))
row=next(r for r in WorkbenchService.Settings(doc) if str(r.Id)==setup['view']);vp=Rhino.Display.RhinoViewport();vp.Size=System.Drawing.Size(480,240);WorkbenchService.ApplyCamera(doc,row,vp,480,240)
xyz=lambda p:[p.X,p.Y,p.Z]
camera=dict(origin=xyz(vp.CameraLocation),right=xyz(vp.CameraX),up=xyz(vp.CameraY),back=xyz(vp.CameraZ),frustum=list(vp.GetFrustum())[1:]);vp.Dispose()
report=dict(pid=EXPECTED_PID,native=native,exports=exports,statePreserved=True,camera=camera)
with open(os.path.join(folder,'object-export.json'),'w') as f:json.dump(report,f,indent=2)
a=api('material_library')['assets'];asset=next(a for a in a if a['id']==setup['asset']['id']);asset['randomization']['mode']='stochastic';asset['randomization']['seed']=77
api('material_update',asset=asset);api('material_tool_select',assetId=asset['id']);api('material_tool_apply')
print(json.dumps(dict(perObjectVariants=True,metricScale=True,objectPsdExported=True,stochasticApplyStarted=True)))

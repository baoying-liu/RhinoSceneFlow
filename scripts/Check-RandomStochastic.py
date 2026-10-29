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
 obj=doc.Objects.FindId(System.Guid(oid));render=obj.GetRenderMaterial(True);material=render.ToMaterial(Rhino.Render.RenderTexture.TextureGeneration.Disallow);texture=material.GetBitmapTexture();mapping=obj.GetTextureMapping(1)
 _,a=mapping.Evaluate(Rhino.Geometry.Point3d(0,0,0),Rhino.Geometry.Vector3d.ZAxis);_,b=mapping.Evaluate(Rhino.Geometry.Point3d(1000,0,0),Rhino.Geometry.Vector3d.ZAxis);a.Transform(texture.UvwTransform);b.Transform(texture.UvwTransform)
 bitmap=System.Drawing.Bitmap(texture.FileName);size=[bitmap.Width,bitmap.Height];bitmap.Dispose();assert size==[512,512] and abs(b.X-a.X-.25)<1e-6,(size,a,b)
 _,c=mapping.Evaluate(Rhino.Geometry.Point3d(0,1000,0),Rhino.Geometry.Vector3d.ZAxis);c.Transform(texture.UvwTransform)
 native.append(dict(id=str(render.Id),path=texture.FileName,size=size,repeatDelta=b.X-a.X,uvBasis=[[p.X,p.Y] for p in [a,b,c]]));texture.Dispose();material.Dispose();mapping.Dispose()
assert native[0]['id']==native[1]['id'],native
api('configure_view',viewId=setup['view'],settings=dict(width=480,height=240,layers=[dict(kind='texture',textureGrouping='material')]))
exports=api('export_workbench',directory=os.path.join(folder,'stochastic'),views=[setup['view']]);assert all(f['ok'] for f in exports['files']),exports
modes=api('workbench_settings')['displayModes'];rendered=next(m for m in modes if m['name']=='Rendered')
api('configure_view',viewId=setup['view'],settings=dict(mode=rendered['id']))
rows=list(WorkbenchService.Settings(doc));row=next(r for r in rows if str(r.Id)==setup['view']);preview=WorkbenchService.Preview(doc,row,700);preview.Save(os.path.join(folder,'native-stochastic.png'),System.Drawing.Imaging.ImageFormat.Png);preview.Dispose()
# Actual metadata model inspects a structured image, without requesting another generated image.
clr.AddReference('RhinoSceneFlow.Core')
from RhinoSceneFlow.Core import MaterialAsset,CodexCatalogRunner
brick=MaterialAsset();brick.Name='Red brick';brick.Prompt='规则红砖墙，清晰砖缝，不能旋转或打乱砖缝。'
image=os.path.abspath(os.path.join(OUTPUT_DIR,'..','random-worker','brick.png'))
task=CodexCatalogRunner.RunAsync(os.path.join(folder,'brick-ai'),'label',brick.Prompt,System.Array[MaterialAsset]([brick]),System.Threading.CancellationToken(False),System.Array[System.String]([image]))
System.AppDomain.CurrentDomain.SetData('Random014BrickAi',task)
report=dict(pid=EXPECTED_PID,native=native,exports=exports,metricDensityPreserved=True,camera=json.load(open(os.path.join(folder,'object-export.json')))['camera'],aiJob=api('material_chat_status',jobId=setup['aiJob']))
with open(os.path.join(folder,'stochastic-export.json'),'w') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(stochasticNativeAndPsd=True,metricDensityPreserved=True,brickAiStarted=True,aiStatus=report['aiJob']['status'])))

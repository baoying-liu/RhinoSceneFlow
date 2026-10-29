"""B-only real cache/UV/RDK/PSD fixture and one actual AI generation request."""
import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;assert doc.Objects.Count==0,'Fresh B document required'
folder=os.path.join(OUTPUT_DIR,'random014');os.makedirs(folder,exist_ok=True)
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
assert api('describe')['version']=='0.14.0'
original=api('material_library')['directory'];library=os.path.join(folder,'lib-'+str(EXPECTED_PID));api('material_configure',directory=library)
doc.ModelUnitSystem=Rhino.UnitSystem.Millimeters
images=os.path.abspath(os.path.join(OUTPUT_DIR,'..','random-worker'))
asset=api('material_import',asset=dict(name='Random014 natural',category='Test',tags=['natural'],widthMeters=1,heightMeters=1,randomization=dict(mode='object',seed=51,strength=.15,tiles=4,rotate=True)),files={s:os.path.join(images,n+'.png') for s,n in [('baseColor','natural'),('normal','normal'),('roughness','roughness')]})
ids=[]
for i in range(2):
 x=i*2500;pts=[Rhino.Geometry.Point3d(x,0,0),Rhino.Geometry.Point3d(x+2000,0,0),Rhino.Geometry.Point3d(x+2000,2000,0),Rhino.Geometry.Point3d(x,2000,0)]
 brep=Rhino.Geometry.Brep.CreateFromCornerPoints(*pts,doc.ModelAbsoluteTolerance);attrs=Rhino.DocObjects.ObjectAttributes();attrs.Name='SceneFlow_Random014_'+str(i);ids.append(str(doc.Objects.AddBrep(brep,attrs)));brep.Dispose()
vp=Rhino.Display.RhinoViewport();vp.Size=System.Drawing.Size(600,300);vp.SetProjection(Rhino.Display.DefinedViewportProjection.Top,'Top',True);vp.ZoomBoundingBox(Rhino.Geometry.BoundingBox(Rhino.Geometry.Point3d(-200,-200,-1),Rhino.Geometry.Point3d(4700,2200,1)))
info=Rhino.DocObjects.ViewInfo(vp);info.Name='Random014Top';index=doc.NamedViews.Add(info);view=str(doc.NamedViews[index].NamedViewId);info.Dispose();vp.Dispose()
api('material_workspace_group');api('material_tool_select',assetId=asset['id']);doc.Objects.UnselectAll()
for oid in ids:doc.Objects.FindId(System.Guid(oid)).Select(True)
api('material_tool_apply')
# The same production chat -> image -> AI label/default path the user runs.
generated=api('material_chat_start',conversation='生成一张浅灰细颗粒混凝土无缝材质，均匀自然，无砖缝、无石块、无明显方向。整张代表一米乘一米。请实际生成新的图片。',reuseSimilar=False)
report=dict(pid=EXPECTED_PID,document=int(doc.RuntimeSerialNumber),originalLibrary=original,library=library,asset=asset,objects=ids,view=view,aiJob=generated['id'])
with open(os.path.join(folder,'setup.json'),'w') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(pid=EXPECTED_PID,objectApplyStarted=True,realAiJob=generated['id'])))

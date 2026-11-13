import Rhino,System,clr,json,os
from System.Drawing import Color
from System.Drawing.Imaging import ImageFormat
from Rhino.Render import RenderMaterial
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi,WorkbenchService,PlantService
D=__rhino_doc__;assert 'material-check-owned.3dm' in D.Path
R=os.path.abspath(os.path.join(OUTPUT_DIR,'..','..'));out=os.path.join(R,'media','tutorial-en','public','case','promo-final-v06');row=next(r for r in WorkbenchService.Settings(D) if r.Name=='Promo Human').Copy();row.Width=1920;row.Height=1080;row.Mode=next(m.Id for m in Rhino.Display.DisplayModeDescription.GetDisplayModes() if m.EnglishName=='Rendered')
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(D.RuntimeSerialNumber),**kw))));assert r['ok'],r;return r['result']
def shot(name):
 b=WorkbenchService.Preview(D,row,1920);b.Save(os.path.join(out,name+'.png'),ImageFormat.Png);b.Dispose()
gid=System.Guid('e6863806-7b87-4140-adf3-3178e35f9500');D.Objects.Hide(gid,True);saved=[(o.Id,o.Attributes.Duplicate(),o.RenderMaterial) for o in D.Objects if not PlantService.IsPlant(o)];native=Rhino.DocObjects.Material();native.DiffuseColor=Color.FromArgb(235,235,230);white=RenderMaterial.FromMaterial(native,D);white.Name='Promo owned white preparation';D.RenderMaterials.Add(white)
for oid,a,m in saved:
 obj=D.Objects.FindId(oid);attrs=obj.Attributes.Duplicate();attrs.MaterialSource=Rhino.DocObjects.ObjectMaterialSource.MaterialFromObject;D.Objects.ModifyAttributes(oid,attrs,True);obj.RenderMaterial=white;obj.CommitChanges()
shot('white-human');target='4271cba2-960c-4f50-a49b-d26ae9b64f08';api('material_apply',assetId='378e3072-9af6-4c5d-9d5f-57042e415f0c',objects=[target]);shot('object-material');layer=next(l for l in D.Layers if 'Cedar' in l.Name);api('material_apply',assetId='378e3072-9af6-4c5d-9d5f-57042e415f0c',layers=[str(layer.Id)]);shot('layer-material')
for oid,a,m in saved:
 obj=D.Objects.FindId(oid);obj.RenderMaterial=m;obj.CommitChanges();D.Objects.ModifyAttributes(oid,a,True)
for key,aid in [('cedar','da8e6581-808e-48ca-8e77-f63885689032'),('brick','bb197acd-2ecf-446f-868e-895d0821e625'),('terracotta','378e3072-9af6-4c5d-57042e415f0c'),('limestone','cb477ed4-4586-4ad7-907f-c6386d2bfd0c')]:
 if key=='terracotta':aid='378e3072-9af6-4c5d-9d5f-57042e415f0c'
 api('material_apply',assetId=aid,layers=[str(layer.Id)]);shot('material-'+key)
api('material_apply',assetId='da8e6581-808e-48ca-8e77-f63885689032',layers=[str(layer.Id)]);D.Objects.Show(gid,True);D.Views.Redraw();print('Captured white, object scope, layer scope and four plant-free material scenes through native APIs; owned copy only.')


import Rhino,System,clr,json,os
from System.Drawing.Imaging import ImageFormat
from Rhino.Render import RenderMaterial
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi,WorkbenchService
D=__rhino_doc__;assert 'material-check-owned.3dm' in D.Path
R=os.path.abspath(os.path.join(OUTPUT_DIR,'..','..'));out=os.path.join(R,'media','tutorial-en','public','case','promo-sample-v05','fixes');os.makedirs(out,exist_ok=True)
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(D.RuntimeSerialNumber),**kw))));assert r['ok'],r;return r['result']
row=next(r for r in WorkbenchService.Settings(D) if r.Name=='Promo Human').Copy();row.Width=1920;row.Height=1080;row.PreviewSeason='summer';row.Mode=next(m.Id for m in Rhino.Display.DisplayModeDescription.GetDisplayModes() if m.EnglishName=='Rendered')
layer=next(l for l in D.Layers if 'Cedar' in l.Name)
target='4271cba2-960c-4f50-a49b-d26ae9b64f08'
def shot(name):
 bmp=WorkbenchService.Preview(D,row,1920);bmp.Save(os.path.join(out,name+'.png'),ImageFormat.Png);bmp.Dispose()
record=[]
for key,aid in [('brick','bb197acd-2ecf-446f-868e-895d0821e625'),('terracotta','378e3072-9af6-4c5d-9d5f-57042e415f0c'),('limestone','cb477ed4-4586-4ad7-907f-c6386d2bfd0c'),('cedar','da8e6581-808e-48ca-8e77-f63885689032')]:
 result=api('material_apply',assetId=aid,layers=[str(layer.Id)]);shot('material-'+key)
 obj=D.Objects.FindId(System.Guid(target));m=obj.GetRenderMaterial(True);tx=m.GetTextureFromUsage(RenderMaterial.StandardChildSlots.PbrBaseColor)
 record.append(dict(key=key,operation='material_apply',asset=aid,repeat=str(tx.GetRepeat()),uv=result))
shot('material-before')
result=api('material_apply',assetId='378e3072-9af6-4c5d-9d5f-57042e415f0c',objects=[target]);shot('material-after')
json.dump(record,open(os.path.join(out,'material-capture.json'),'w'),indent=2)
print(json.dumps([dict(key=r['key'],repeat=r['repeat']) for r in record]))

import Rhino,System,clr,json,os
from System.Reflection import BindingFlags
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import PlantService,WorkbenchService
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
folder=os.path.join(OUTPUT_DIR,'plants015');setup=json.load(open(os.path.join(folder,'setup.json')))
conduit=clr.GetClrType(PlantService).GetField('conduit',BindingFlags.NonPublic|BindingFlags.Static).GetValue(None)
materials=conduit.GetType().GetField('materials',BindingFlags.NonPublic|BindingFlags.Instance).GetValue(conduit)
paths=list(materials.Keys)
for path in paths:
 materials[path].Dispose();m=Rhino.DocObjects.Material();m.ToPhysicallyBased();m.PhysicallyBased.BaseColor=Rhino.Display.Color4f.White;m.PhysicallyBased.UseBaseColorTextureAlphaForObjectAlphaTransparencyTexture=True
 texture=Rhino.DocObjects.Texture();texture.FileName=path;texture.Enabled=True;m.PhysicallyBased.SetTexture(texture,Rhino.DocObjects.TextureType.PBR_BaseColor)
 material=Rhino.Display.DisplayMaterial(m);material.IsTwoSided=True;materials[path]=material;texture.Dispose();m.Dispose()
row=next(r for r in WorkbenchService.Settings(__rhino_doc__) if str(r.Id)==setup['view']);row.Mode=Rhino.Display.DisplayModeDescription.RenderedId
bitmap=WorkbenchService.Preview(__rhino_doc__,row,720);bitmap.Save(os.path.join(folder,'native-pbr-probe.png'),System.Drawing.Imaging.ImageFormat.Png);bitmap.Dispose()
print('PBR alpha probe')

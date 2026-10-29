import Rhino,System,clr,json,os
from System.Reflection import BindingFlags
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import PlantService,WorkbenchService
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
folder=os.path.join(OUTPUT_DIR,'plants015');receipt=json.load(open(os.path.join(folder,'delivery.json')))
conduit=clr.GetClrType(PlantService).GetField('conduit',BindingFlags.NonPublic|BindingFlags.Static).GetValue(None);materials=conduit.GetType().GetField('materials',BindingFlags.NonPublic|BindingFlags.Instance).GetValue(conduit)
old={}
for path in list(materials.Keys):
 old[path]=materials[path];m=Rhino.Display.DisplayMaterial(System.Drawing.Color.White,.5);m.IsTwoSided=True;m.BackTransparency=.5
 texture=Rhino.DocObjects.Texture();texture.FileName=path;texture.Enabled=True;texture.TextureCombineMode=Rhino.DocObjects.TextureCombineMode.Blend;texture.SetAlphaBlendValues(0,0,1,0,0);texture.SetRGBBlendValues(System.Drawing.Color.Black,0,1,0,0)
 m.SetBitmapTexture(texture,True);m.SetBitmapTexture(texture,False);texture.Dispose();materials[path]=m
try:
 row=next(r for r in WorkbenchService.Settings(__rhino_doc__) if str(r.Id)==receipt['views'][1]);row.Mode=Rhino.Display.DisplayModeDescription.RenderedId;b=WorkbenchService.Preview(__rhino_doc__,row,900);b.Save(os.path.join(folder,'native-blend-probe.png'),System.Drawing.Imaging.ImageFormat.Png);b.Dispose()
finally:
 for path,m in old.items():materials[path].Dispose();materials[path]=m
print('Classic explicit texture-alpha blend probed; materials restored')

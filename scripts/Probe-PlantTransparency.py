import Rhino,System,clr,json,os
from System.Reflection import BindingFlags
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import PlantService,WorkbenchService,McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
folder=os.path.join(OUTPUT_DIR,'plants015');setup=json.load(open(os.path.join(folder,'setup.json')))
conduit=clr.GetClrType(PlantService).GetField('conduit',BindingFlags.NonPublic|BindingFlags.Static).GetValue(None)
materials=conduit.GetType().GetField('materials',BindingFlags.NonPublic|BindingFlags.Instance).GetValue(conduit)
for pair in materials:
 path=pair.Key;alpha=path+'.transparency-test.png'
 source=System.Drawing.Bitmap(path);bitmap=System.Drawing.Bitmap(source.Width,source.Height)
 for y in range(source.Height):
  for x in range(source.Width):
   value=255-source.GetPixel(x,y).A;bitmap.SetPixel(x,y,System.Drawing.Color.FromArgb(value,value,value))
 bitmap.Save(alpha,System.Drawing.Imaging.ImageFormat.Png);source.Dispose();bitmap.Dispose()
 pair.Value.SetTransparencyTexture(alpha,True);pair.Value.SetTransparencyTexture(alpha,False)
row=next(r for r in WorkbenchService.Settings(__rhino_doc__) if str(r.Id)==setup['view']);row.Mode=Rhino.Display.DisplayModeDescription.RenderedId
bitmap=WorkbenchService.Preview(__rhino_doc__,row,720);bitmap.Save(os.path.join(folder,'native-alpha-probe.png'),System.Drawing.Imaging.ImageFormat.Png);bitmap.Dispose()
print('Explicit transparency map tested without restarting or touching the active AI job')

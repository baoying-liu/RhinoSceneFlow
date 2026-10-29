import Rhino,System,clr,json,os
from System.Reflection import BindingFlags
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import PlantService,WorkbenchService
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
folder=os.path.join(OUTPUT_DIR,'plants015');receipt=json.load(open(os.path.join(folder,'delivery.json')))
conduit=clr.GetClrType(PlantService).GetField('conduit',BindingFlags.NonPublic|BindingFlags.Static).GetValue(None);materials=conduit.GetType().GetField('materials',BindingFlags.NonPublic|BindingFlags.Instance).GetValue(conduit)
for pair in materials:pair.Value.Transparency=.001;pair.Value.BackTransparency=.001
row=next(r for r in WorkbenchService.Settings(__rhino_doc__) if str(r.Id)==receipt['views'][1]);row.Mode=Rhino.Display.DisplayModeDescription.RenderedId
b=WorkbenchService.Preview(__rhino_doc__,row,900);b.Save(os.path.join(folder,'native-alpha-pass-probe.png'),System.Drawing.Imaging.ImageFormat.Png);b.Dispose()
for pair in materials:pair.Value.Transparency=0;pair.Value.BackTransparency=0
print('Explicit blended display pass probed and restored')

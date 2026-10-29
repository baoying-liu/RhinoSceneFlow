import Rhino,System,clr,json,os
from System.Reflection import BindingFlags
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import PlantService,WorkbenchService
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
folder=os.path.join(OUTPUT_DIR,'plants015');delivery=json.load(open(os.path.join(folder,'delivery.json')))
flags=BindingFlags.NonPublic|BindingFlags.Instance|BindingFlags.Static
old=clr.GetClrType(PlantService).GetField('conduit',flags).GetValue(None);draw=old.GetType().GetMethod('PostDrawObjects',flags);box=old.GetType().GetMethod('CalculateBoundingBox',flags)
class DepthProbe(Rhino.Display.DisplayConduit):
 calls=0
 def PreDrawObject(self,e):
  if PlantService.IsPlant(e.RhinoObject):e.DrawObject=False
 def CalculateBoundingBox(self,e):box.Invoke(old,System.Array[System.Object]([e]))
 def PostDrawObjects(self,e):
  self.calls+=1
  e.Display.PushDepthWriting(False)
  try:draw.Invoke(old,System.Array[System.Object]([e]))
  finally:e.Display.PopDepthWriting()
probe=DepthProbe();old.Enabled=False;probe.Enabled=True
try:
 row=next(r for r in WorkbenchService.Settings(__rhino_doc__) if str(r.Id)==delivery['views'][1]);b=WorkbenchService.Preview(__rhino_doc__,row,900);b.Save(os.path.join(folder,'native-depth-probe.png'),System.Drawing.Imaging.ImageFormat.Png);b.Dispose()
finally:probe.Enabled=False;old.Enabled=True
print('Depth writing probe calls: '+str(probe.calls))

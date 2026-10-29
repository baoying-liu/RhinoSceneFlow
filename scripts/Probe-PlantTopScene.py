import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import PlantService,WorkbenchService
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'plants015');delivery=json.load(open(os.path.join(folder,'delivery.json')))
row=next(r for r in WorkbenchService.Settings(doc) if str(r.Id)==delivery['views'][1]);named=next(v for v in doc.NamedViews if str(v.NamedViewId)==delivery['views'][1]);print(json.dumps(dict(cameraDirection=[named.Viewport.CameraDirection.X,named.Viewport.CameraDirection.Y,named.Viewport.CameraDirection.Z])))
modified=doc.Modified;hidden=[];oid=None
try:
 for obj in doc.Objects:
  if not PlantService.IsPlant(obj) and not obj.IsHidden:doc.Objects.Hide(obj.Id,True);hidden.append(obj.Id)
 row.Mode=Rhino.Display.DisplayModeDescription.RenderedId;b=WorkbenchService.Preview(doc,row,900);b.Save(os.path.join(folder,'native-top-no-background.png'),System.Drawing.Imaging.ImageFormat.Png);b.Dispose()
finally:
 for id in hidden:doc.Objects.Show(id,True)
 doc.Modified=modified
print('Native top captured with only plant anchors; non-plant visibility restored')

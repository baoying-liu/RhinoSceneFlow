"""B-only camera writeback on a disposable Named View and complete card layout capture."""
import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import ExportPanelController,WorkbenchService
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;p=ExportPanelController.Find(doc.RuntimeSerialNumber);assert p is not None
folder=os.path.join(OUTPUT_DIR,'workbench');name='SceneFlow_Writeback_'+str(System.Guid.NewGuid())[:8]
def trace(stage):
 with open(os.path.join(folder,'details-progress.txt'),'a') as f:f.write(stage+'\n')
trace('start')
modified=doc.Modified;sun=int(doc.RenderSettings.Sun.Hash);count=doc.NamedViews.Count
view=Rhino.DocObjects.ViewInfo(doc.Views.ActiveView.ActiveViewport);view.Name=name
index=doc.NamedViews.Add(view);view.Dispose();assert index>=0
trace('added')
try:
 old=doc.NamedViews[index];old_direction=old.Viewport.CameraDirection;id=old.NamedViewId;old.Dispose()
 row=next(r for r in WorkbenchService.Settings(doc) if r.Id==id);row.Camera.Yaw=15;row.Camera.Pitch=5;row.Camera.Zoom=1.4
 WorkbenchService.WriteBack(doc,row)
 trace('written')
 assert doc.NamedViews.Count==count+1 and row.Camera.Yaw==0 and row.Camera.Zoom==1
 named=doc.NamedViews[doc.NamedViews.FindByName(name)]
 angle=Rhino.Geometry.Vector3d.VectorAngle(old_direction,named.Viewport.CameraDirection);named.Dispose();assert angle>.01
 assert int(doc.RenderSettings.Sun.Hash)==sun
finally:
 index=doc.NamedViews.FindByName(name)
 if index>=0:assert doc.NamedViews.Delete(index)
 doc.Modified=modified
assert doc.NamedViews.Count==count
trace('writeback-verified')
for row in p.Views:p.RefreshCard(row.Id)
trace('previews-refreshed')
clr.AddReference('PresentationCore');clr.AddReference('PresentationFramework');clr.AddReference('WindowsBase')
from System.Windows import Size,Rect
from System.Windows.Media import PixelFormats
from System.Windows.Media.Imaging import RenderTargetBitmap,PngBitmapEncoder,BitmapFrame
window=p.ControlObject;root=window.Content
root.Measure(Size(1210,880));root.Arrange(Rect(0,0,1210,880));root.UpdateLayout()
trace('layout-arranged')
bitmap=RenderTargetBitmap(1210,880,96,96,PixelFormats.Pbgra32);bitmap.Render(root)
trace('layout-rendered')
encoder=PngBitmapEncoder();encoder.Frames.Add(BitmapFrame.Create(bitmap));path=os.path.join(folder,'cards-layout.png')
stream=System.IO.FileStream(path,System.IO.FileMode.Create)
try:encoder.Save(stream)
finally:stream.Dispose()
report=dict(pid=EXPECTED_PID,writeback=True,writebackAngle=angle,namedCountRestored=True,sunUnchanged=True,layout=path)
with open(os.path.join(folder,'details-verified.json'),'w') as f:json.dump(report,f,indent=2)
print(json.dumps(report))

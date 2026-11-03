"""Native rendered viewport captures; mode/camera and document data must be restored."""
import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'plant-edit0172');root='73fb8208-d869-4935-bb7e-23a6e81e4641'
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
api('plant_edit_exit');view=doc.Views.ActiveView;vp=view.ActiveViewport;saved=Rhino.DocObjects.ViewportInfo(vp);mode=vp.DisplayMode;modified=doc.Modified
def capture(name):
 b=view.CaptureToBitmap(System.Drawing.Size(1000,750),vp.DisplayMode.DisplayAttributes);assert b is not None;b.Save(os.path.join(folder,name+'.png'),System.Drawing.Imaging.ImageFormat.Png);b.Dispose()
try:
 doc.NamedViews.Restore(0,view,False);vp.DisplayMode=Rhino.Display.DisplayModeDescription.GetDisplayMode(Rhino.Display.DisplayModeDescription.RenderedId);doc.Objects.UnselectAll();view.Redraw()
 attrs=vp.DisplayMode.DisplayAttributes;before=[str(attrs.LockedObjectUsage),attrs.LockedColor.ToArgb(),attrs.LockedObjectTransparency,attrs.GhostLockedObjects,attrs.LockedObjectsDrawBehindOthers,attrs.LayersFollowLockUsage]
 capture('rendered-before');api('plant_edit_enter',groupId=root);capture('rendered-isolated');api('plant_edit_exit');doc.Objects.UnselectAll();capture('rendered-after')
 attrs=vp.DisplayMode.DisplayAttributes;after=[str(attrs.LockedObjectUsage),attrs.LockedColor.ToArgb(),attrs.LockedObjectTransparency,attrs.GhostLockedObjects,attrs.LockedObjectsDrawBehindOthers,attrs.LayersFollowLockUsage];assert after==before,'Mode was permanently changed'
 json.dump(dict(pid=EXPECTED_PID,modeRestored=True,before=before,after=after),open(os.path.join(folder,'grey.json'),'w'),indent=2)
finally:
 api('plant_edit_exit');vp.SetViewProjection(saved,True);vp.DisplayMode=mode;doc.Modified=modified;view.Redraw()

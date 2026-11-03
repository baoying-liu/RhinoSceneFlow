"""Owned plane verifies front occlusion, wireframe mode and per-object overrides."""
import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi,PlantEditing
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'plant-edit0172');receipt=json.load(open(os.path.join(folder,'backup.json')));assert doc.Path==receipt['backup']
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
api('plant_edit_exit');vp=doc.Views.ActiveView.ActiveViewport;mode=vp.DisplayMode;modified=doc.Modified;testId=System.Guid.Empty
try:
 vp.DisplayMode=Rhino.Display.DisplayModeDescription.GetDisplayMode(Rhino.Display.DisplayModeDescription.RenderedId)
 api('plant_edit_enter',groupId='73fb8208-d869-4935-bb7e-23a6e81e4641')
 x,y,_=json.load(open(os.path.join(folder,'interaction.json')))['faintLeafHit'];hit=PlantEditing.Pick(doc,vp,x,y);assert hit is not None
 ok,line=vp.GetFrustumLine(x,y)
 if line.Direction*vp.CameraDirection<0:line.Flip()
 direction=line.Direction;direction.Unitize();p=line.From+direction*(hit.Distance-1);right=vp.CameraX;up=vp.CameraY
 mesh=Rhino.Geometry.Mesh()
 for q in [p-right-up,p+right-up,p+right+up,p-right+up]:mesh.Vertices.Add(q)
 mesh.Faces.AddFace(0,1,2,3);mesh.Normals.ComputeNormals();attrs=Rhino.DocObjects.ObjectAttributes();attrs.Name='Owned plant-pick regression plane';attrs.Mode=Rhino.DocObjects.ObjectMode.Locked
 testId=doc.Objects.AddMesh(mesh,attrs);mesh.Dispose();assert testId!=System.Guid.Empty
 assert PlantEditing.Pick(doc,vp,x,y) is None,'Foreground surface must block the plant'
 attrs=doc.Objects.FindId(testId).Attributes.Duplicate();attrs.SetDisplayModeOverride(Rhino.Display.DisplayModeDescription.GetDisplayMode(Rhino.Display.DisplayModeDescription.WireframeId),vp.Id);assert doc.Objects.ModifyAttributes(testId,attrs,True)
 assert PlantEditing.Pick(doc,vp,x,y).IndividualId==hit.IndividualId,'Object wire override must not block like a solid'
 vp.DisplayMode=Rhino.Display.DisplayModeDescription.GetDisplayMode(Rhino.Display.DisplayModeDescription.WireframeId)
 assert PlantEditing.Pick(doc,vp,x,y) is not None,'Wire viewport must allow selection through context surfaces'
 json.dump(dict(pid=EXPECTED_PID,foregroundBlocks=True,objectWireOverrideRespected=True,wireViewportPick=True),open(os.path.join(folder,'occlusion.json'),'w'),indent=2)
 print('Front/behind occlusion and wireframe override passed')
finally:
 if testId!=System.Guid.Empty:
  doc.Objects.Unlock(testId,True);assert doc.Objects.Delete(testId,True)
 api('plant_edit_exit');vp.DisplayMode=mode;doc.Modified=modified;doc.Views.Redraw()

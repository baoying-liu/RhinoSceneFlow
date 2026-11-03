"""Use a separate white-background Rendered mode; preserve the user's built-in modes."""
import Rhino,System,clr,json,os
from System.Drawing import Color
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi,WorkbenchService
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.abspath(os.path.join(OUTPUT_DIR,'..','examples','Hillside-Retreat'));data=json.load(open(os.path.join(folder,'geometry.json')))
assert int(doc.RuntimeSerialNumber)==data['document']
name='SceneFlow Demo - Rendered'
mode=next((m for m in Rhino.Display.DisplayModeDescription.GetDisplayModes() if m.EnglishName==name),None)
if mode is None:
 id=Rhino.Display.DisplayModeDescription.CopyDisplayMode(Rhino.Display.DisplayModeDescription.RenderedId,name);mode=Rhino.Display.DisplayModeDescription.GetDisplayMode(id)
mode.DisplayAttributes.SetFill(Color.White);mode.DisplayAttributes.ShowSurfaceEdges=False;mode.DisplayAttributes.MeshSpecificAttributes.ShowMeshWires=False
assert Rhino.Display.DisplayModeDescription.UpdateDisplayMode(mode)
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
arctic=next(m for m in Rhino.Display.DisplayModeDescription.GetDisplayModes() if m.EnglishName=='Arctic')
for row in api('named_views'):
 api('configure_view',viewId=row['id'],settings=dict(width=1600,height=1200,mode=str(mode.Id),sun=dict(useDocument=False,azimuth=135,altitude=42),layers=[dict(kind='plants',plantGrouping='species'),dict(kind='shadow',blend='mul ',opacity=45),dict(kind='texture',textureGrouping='material'),dict(kind='display',mode=str(arctic.Id))],plantShadows=True))
doc.Views.ActiveView.ActiveViewport.DisplayMode=mode;doc.Views.Redraw()
with open(os.path.join(folder,'display.json'),'w') as f:json.dump(dict(mode=str(mode.Id),name=name,arctic=str(arctic.Id)),f,indent=2)
b=WorkbenchService.Preview(doc,WorkbenchService.Settings(doc)[0],1000);b.Save(os.path.join(folder,'geometry-preview-clean.png'),System.Drawing.Imaging.ImageFormat.Png);b.Dispose()
options=Rhino.FileIO.FileWriteOptions();options.UpdateDocumentPath=True;options.SuppressDialogBoxes=True
assert doc.WriteFile(json.load(open(os.path.join(folder,'views.json')))['model'],options)
print(json.dumps(dict(mode=name,views=3,saved=True)))

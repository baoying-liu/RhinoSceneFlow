import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin');clr.AddReference('PresentationCore');clr.AddReference('PresentationFramework');clr.AddReference('WindowsBase')
from RhinoSceneFlow.Plugin import McpApi,WorkbenchService,ExportPanelController
from System.Windows import Size,Rect
from System.Windows.Media import PixelFormats
from System.Windows.Media.Imaging import RenderTargetBitmap,PngBitmapEncoder,BitmapFrame
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'plants016');receipt=json.load(open(os.path.join(folder,'delivery.json')))
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
state=api('plant_group_state',groupId=receipt['group']);assert not state['busy'] and state['error'] is None and state['count']==12 and state['manual']==2,state
doc.Objects.UnselectAll();vp=doc.Views.ActiveView.ActiveViewport;vp.DisplayMode=Rhino.Display.DisplayModeDescription.GetDisplayMode(Rhino.Display.DisplayModeDescription.RenderedId);vp.SetCameraLocation(Rhino.Geometry.Point3d(29,-25,25),False);vp.SetCameraTarget(Rhino.Geometry.Point3d(10,10,3),False);vp.ZoomExtents();doc.Views.Redraw()
index=doc.NamedViews.Add('Planting Composition',vp.Id);view=str(doc.NamedViews[index].Viewport.Id)
ExportPanelController.Open(doc).RefreshNamedViews()
assert any(str(r.Id)==view for r in WorkbenchService.Settings(doc))
for grouping in ['individual','species','all']:
 api('configure_view',viewId=view,settings=dict(width=1000,height=700,mode=str(Rhino.Display.DisplayModeDescription.RenderedId),layers=[dict(kind='plants',plantGrouping=grouping),dict(kind='shadow',blend='mul '),dict(kind='material')],plantShadows=True))
 report=api('export_workbench',directory=os.path.join(receipt['examples'],grouping),views=[view],collision='overwrite');assert all(f['ok'] for f in report['files']),report;receipt[grouping]=report
row=next(r for r in WorkbenchService.Settings(doc) if str(r.Id)==view);b=WorkbenchService.Preview(doc,row,900);b.Save(os.path.join(receipt['examples'],'native.png'),System.Drawing.Imaging.ImageFormat.Png);b.Dispose()
api('material_workspace_open',page='planting');doc.Objects.Select(System.Guid(receipt['group']));doc.Views.Redraw();ui=api('material_workspace_status');assert len(ui['tools'])==5 and all(t['error'] is None for t in ui['tools'].values()),ui
panel=Rhino.UI.Panels.GetPanel(System.Guid(ui['pages'][3]['panelId']));control=panel.ControlObject;control.Measure(Size(420,1000));control.Arrange(Rect(0,0,420,1000));control.UpdateLayout();bitmap=RenderTargetBitmap(630,1500,144,144,PixelFormats.Pbgra32);bitmap.Render(control);encoder=PngBitmapEncoder();encoder.Frames.Add(BitmapFrame.Create(bitmap));stream=System.IO.FileStream(os.path.join(receipt['examples'],'panel.png'),System.IO.FileMode.Create)
try:encoder.Save(stream)
finally:stream.Dispose()
options=Rhino.FileIO.FileWriteOptions();options.UpdateDocumentPath=True;options.SuppressDialogBoxes=True;receipt['model']=os.path.join(receipt['examples'],'SceneFlow-Planting-Composition.3dm');assert doc.WriteFile(receipt['model'],options) and not doc.Modified
receipt.update(pid=EXPECTED_PID,count=state['count'],manual=state['manual'],view=view,allToolsHealthy=True)
with open(os.path.join(folder,'delivery.json'),'w') as f:json.dump(receipt,f,indent=2)
print(json.dumps(receipt))

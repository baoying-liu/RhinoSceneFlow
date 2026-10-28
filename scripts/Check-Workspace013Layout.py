"""Read final native control bounds, capture shelf, then expand only this owned native container."""
import Rhino,System,clr,json,os
from System.Reflection import BindingFlags
clr.AddReference('RhinoSceneFlow.Plugin');clr.AddReference('PresentationCore');clr.AddReference('PresentationFramework');clr.AddReference('WindowsBase')
from RhinoSceneFlow.Plugin import McpApi
from Eto.Drawing import Size as EtoSize
from System.Windows.Media import PixelFormats
from System.Windows.Media.Imaging import RenderTargetBitmap,PngBitmapEncoder,BitmapFrame
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
folder=os.path.join(OUTPUT_DIR,'workspace013');s=json.loads(McpApi.Execute('{"apiVersion":1,"operation":"material_workspace_status"}'))['result']
p=Rhino.UI.Panels.GetPanel(System.Guid(s['pages'][0]['panelId']));flags=BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Static|BindingFlags.Instance
tool=p.GetType().GetProperty('Tool',flags).GetValue(p);assert tool.Width<680 and tool.Content.GetType().Name!='Splitter',(tool.Width,tool.Content);narrowWidth=tool.Width
root=p.ControlObject;bitmap=RenderTargetBitmap(max(1,int(root.ActualWidth*1.5)),max(1,int(root.ActualHeight*1.5)),144,144,PixelFormats.Pbgra32);bitmap.Render(root);encoder=PngBitmapEncoder();encoder.Frames.Add(BitmapFrame.Create(bitmap));stream=System.IO.FileStream(os.path.join(folder,'final-library.png'),System.IO.FileMode.Create);encoder.Save(stream);stream.Dispose()
asm=next(a for a in System.AppDomain.CurrentDomain.GetAssemblies() if a.GetName().Name=='Rhino.UI');registry=asm.GetType('Rhino.UI.Internal.TabPanels.TabPanelDockBars');bar=registry.GetMethod('FromDockBarId',flags).Invoke(None,System.Array[System.Object]([System.Guid(s['pages'][0]['dockBars'][0])]))
form=bar.GetType().GetMethod('HasFloatingForm',flags).Invoke(bar,System.Array[System.Object]([System.UInt32(__rhino_doc__.RuntimeSerialNumber)]));assert form
System.AppDomain.CurrentDomain.SetData('Workspace013LayoutOriginal',form.ClientSize);form.ClientSize=EtoSize(850,900)
print(json.dumps(dict(narrowWidth=narrowWidth,expandRequested=True)))

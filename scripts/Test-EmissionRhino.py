"""Run through Rhino-Mcp.py, on a fresh B document only. No image-model calls."""
import Rhino,System,clr,json,os
from System.Drawing import Color,Bitmap
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=Rhino.RhinoDoc.ActiveDoc
assert not list(doc.Objects) and not doc.Modified,'Use a fresh empty B document; never clear user work.'
def api(op,**kw):
    r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
    assert r['ok'],r
    return r['result']
assert api('describe')['version']=='0.23.4'
doc.ModelUnitSystem=Rhino.UnitSystem.Meters
g=Rhino.Geometry
folder=os.path.join(OUTPUT_DIR,'emission0234');os.makedirs(folder,exist_ok=True)
def box(name,x0,y0,z0,x1,y1,z1):
    a=Rhino.DocObjects.ObjectAttributes();a.Name=name
    return str(doc.Objects.AddBrep(g.BoundingBox(g.Point3d(x0,y0,z0),g.Point3d(x1,y1,z1)).ToBrep(),a))
first=box('Warm emitter',-2,0,1,-.6,.3,3);second=box('Cool emitter',.6,0,1,2,.3,3)
wall=box('Opaque foreground',-2.1,-.8,.5,-1.4,-.6,3.5)
floor=box('Ground',-4,-2,-.3,4,3,0)
source=os.path.join(folder,'emission-albedo.png');image=Bitmap(8,8)
for y in range(8):
    for x in range(8):image.SetPixel(x,y,Color.FromArgb(180,180,180))
image.Save(source);image.Dispose()
asset=api('material_import',asset=dict(name='Emission B fixture',widthMeters=1,heightMeters=1,emission=dict(enabled=True,color='#FFBB66',intensity=2)),files=dict(baseColor=source))
api('material_apply',assetId=asset['id'],objects=[first,second],mapping=dict(mode='box'))
before=api('selection_properties',objects=[first,second])
api('selection_material_update',objects=[second],scope='object',emission=dict(enabled=True,color='#5599FF',intensity=3))
after=api('selection_properties',objects=[first,second])
assert after['objects'][0]['emission']['enabled'] and after['objects'][1]['emission']['enabled'],after
assert after['objects'][0]['material']!=after['objects'][1]['material'],'Shared material was not isolated.'
assert after['objects'][0]['emission']['color']!=after['objects'][1]['emission']['color'],after
vp=doc.Views.ActiveView.ActiveViewport
vp.SetCameraLocations(g.Point3d(0,0,1.6),g.Point3d(0,-13,5))
vp.ZoomBoundingBox(doc.Objects.BoundingBoxVisible)
vp.DisplayMode=Rhino.Display.DisplayModeDescription.GetDisplayMode(Rhino.Display.DisplayModeDescription.RenderedId)
view=api('workbench_create_view',name='Emission demonstration')['viewId']
outputs=[]
for grouping,glow in [('all',False),('object',False),('all',True),('object',True)]:
    api('configure_view',viewId=view,settings=dict(width=512,height=384,layers=[dict(kind='emission',textureGrouping=grouping,glow=glow,blend='hLit'),dict(kind='color',textureGrouping='all')]))
    state=(doc.Modified,str(vp.CameraLocation),str(vp.CameraDirection),str(vp.DisplayMode.Id),[(str(o.Id),int(o.Geometry.DataCRC(0))) for o in doc.Objects])
    result=api('export_workbench',views=[view],directory=os.path.join(folder,grouping+('-glow' if glow else '-source')),collision='number');outputs.append(result)
    assert state==(doc.Modified,str(vp.CameraLocation),str(vp.CameraDirection),str(vp.DisplayMode.Id),[(str(o.Id),int(o.Geometry.DataCRC(0))) for o in doc.Objects]),'Export mutated document/view'
api('material_workspace_open',page='properties')
receipt=dict(pid=EXPECTED_PID,document=int(doc.RuntimeSerialNumber),asset=asset['id'],objects=[first,second,wall,floor],before=before,after=after,view=view,exports=outputs)
with open(os.path.join(folder,'receipt.json'),'w') as f:json.dump(receipt,f,indent=2)
doc.Views.Redraw()
print('CHECK:'+json.dumps(receipt))

import Rhino,System,clr,json,os
from System.Drawing import Color,Bitmap
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.abspath(os.path.join(OUTPUT_DIR,'..','examples','Hillside-Retreat'));data=json.load(open(os.path.join(folder,'geometry.json')));tree=json.load(open(os.path.join(folder,'tree-state.json')))
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
assert tree['status']=='completed' and tree['plant']
path=os.path.join(folder,'planting.json');assert not os.path.exists(path),'Preserve existing planted group.'
asset=next(a for a in api('plant_library')['assets'] if a['id']==tree['plant'])
area=Rhino.Geometry.AreaMassProperties.Compute(doc.Objects.FindId(System.Guid(data['carrier'])).Geometry)
try:density=15.0/area.Area
finally:area.Dispose()
group=api('plant_group_create',spec=dict(name='Hillside river birch / 河桦种植',surface=data['carrier'],palette=[dict(asset=asset['id'],weight=1,spacingMeters=5.5)],settings=dict(density=density,layoutSeed=2038,sizeSeed=105,mirrorSeed=82,minScale=.75,maxScale=1.25,edgeDistance=1.8,edgeStrength=.35,edgeCurve=[0,.2,.55,.85,1])))['id']
for p in [[-20,-12,0],[19,-9,0],[-16,17,0],[17,17,0]]:api('plant_group_manual',groupId=group,assetId=asset['id'],point=p)
li=doc.Layers.Add('12 Planting - River Birch Group',Color.FromArgb(93,139,87));api('plant_group_manage',groups=[group],layerId=str(doc.Layers[li].Id))
api('plant_settings',settings=dict(mode='auto',angle=60,transition=5))
api('plant_select',assetId=asset['id']);api('plant_ui_settings',settings=dict(language='zh',libraryView='tiles',compositionView='tiles'))
with open(path,'w') as f:json.dump(dict(group=group,asset=asset,carrier=data['carrier']),f,indent=2)
# Flat utility colors still go through the shipped import/UV/application APIs.
solids={}
for key,rgb,rough in [('earth',(93,99,72),.95),('gravel',(136,139,129),.95),('contours',(237,231,204),.9),('glass',(94,117,124),.36),('frames',(45,53,53),.65)]:
 p=os.path.join(folder,key+'-swatch.png');b=Bitmap(8,8)
 for y in range(8):
  for x in range(8):b.SetPixel(x,y,Color.FromArgb(*rgb))
 b.Save(p,System.Drawing.Imaging.ImageFormat.Png);b.Dispose()
 a=api('material_import',asset=dict(name='Demo '+key,category='演示 / 色板',tags=['演示',key],roughness=rough,widthMeters=1,heightMeters=1,source='demo-flat-color'),files=dict(baseColor=p));solids[key]=a['id']
 result=api('material_apply',assetId=a['id'],objects=data['materialsets'][key],mapping=dict(mode='box'))
with open(os.path.join(folder,'solids.json'),'w') as f:json.dump(solids,f,indent=2)
doc.Objects.UnselectAll();doc.Views.Redraw();print(json.dumps(dict(group=group,plant=asset['id'],state=api('plant_group_state',groupId=group),solids=solids)))

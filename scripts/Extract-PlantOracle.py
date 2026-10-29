import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi,WorkbenchService
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'plants015');setup=json.load(open(os.path.join(folder,'setup.json')))
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
row=next(r for r in WorkbenchService.Settings(doc) if str(r.Id)==setup['view']);vp=Rhino.Display.RhinoViewport();vp.Size=System.Drawing.Size(row.Width,row.Height);WorkbenchService.ApplyCamera(doc,row,vp,row.Width,row.Height)
vec=lambda p:[p.X,p.Y,p.Z]
_,l,r,b,t,n,f=vp.GetFrustum()
camera=dict(origin=vec(vp.CameraLocation),right=vec(vp.CameraX),up=vec(vp.CameraY),back=vec(vp.CameraZ),frustum=[l,r,b,t,n,f],parallel=vp.IsParallelProjection);vp.Dispose()
plants=api('plant_instances')['objects']
api('configure_view',viewId=setup['view'],settings=dict(layers=[dict(kind='shadow')],plantShadows=False))
off=api('export_workbench',directory=os.path.join(folder,'shadow-without-plants'),views=[setup['view']]);assert all(f['ok'] for f in off['files']),off
api('configure_view',viewId=setup['view'],settings=dict(layers=[dict(kind='plants',plantGrouping='species'),dict(kind='shadow',blend='mul '),dict(kind='texture')],plantShadows=True))
with open(os.path.join(folder,'oracle-scene.json'),'w') as out:json.dump(dict(camera=camera,plants=plants,width=row.Width,height=row.Height,settings=api('plant_settings'),shadowWithout=off),out,indent=2)
print('Owned camera/plant data and shadow-without-plants control exported')

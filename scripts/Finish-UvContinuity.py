import Rhino,System,clr,json,os
from Rhino.Geometry import BoundingBox,Point3d
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'uv-v012');s=json.load(open(os.path.join(folder,'tube-start.json')))
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))));assert r['ok'],r;return r['result']
j=api('material_unwrap_status',jobId=s['tubeJob']['id']);assert j['status']=='completed',j;assert j['results'][0]['charts']==1 and j['results'][0]['stretchMax']<1.6
api('material_apply',assetId=s['asset'],objects=[s['ids'][1]])
proof=api('material_uv_renderer',objectId=s['ids'][1]);assert all(p['uvError']<1e-6 and p['normalError']<1e-6 and p['volume']>0 for p in proof['primitives']);s['rendererProof'].append(proof)
doc.Objects.Hide(System.Guid(s['guide']),True);scale=s['scale'];views=[]
for label,offset in [('Atlas',0),('Tube',30)]:
 vp=Rhino.Display.RhinoViewport();vp.Size=System.Drawing.Size(1200,900);vp.SetProjection(Rhino.Display.DefinedViewportProjection.Perspective,label,True)
 vp.SetCameraLocations(Point3d((100+offset)*scale,100*scale,4*scale),Point3d((123+offset)*scale,70*scale,26*scale));vp.ZoomBoundingBox(BoundingBox(Point3d((90+offset)*scale,90*scale,0),Point3d((110+offset)*scale,110*scale,9*scale)))
 info=Rhino.DocObjects.ViewInfo(vp);info.Name='UV012_'+label;ix=doc.NamedViews.Add(info);views.append(str(doc.NamedViews[ix].NamedViewId));info.Dispose();vp.Dispose()
for id,crc in zip(s['ids'],s['crc']):assert int(doc.Objects.FindId(System.Guid(id)).Geometry.DataCRC(0))==crc
s.update(tubeResult=j,views=views)
with open(os.path.join(folder,'ready.json'),'w') as f:json.dump(s,f,indent=2)
ix=next(i for i in range(doc.NamedViews.Count) if str(doc.NamedViews[i].NamedViewId)==views[1]);doc.NamedViews.Restore(ix,doc.Views.ActiveView.ActiveViewport);doc.Views.ActiveView.ActiveViewport.DisplayMode=Rhino.Display.DisplayModeDescription.GetDisplayMode(Rhino.Display.DisplayModeDescription.RenderedId);doc.Views.Redraw()
print(json.dumps(j));print(json.dumps(api('material_uv_renderer')))

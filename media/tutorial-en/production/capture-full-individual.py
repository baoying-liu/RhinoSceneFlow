import Rhino,System,clr,json,os,math
from System.Drawing.Imaging import ImageFormat
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi,WorkbenchService
D=__rhino_doc__;assert 'material-check-owned.3dm' in D.Path
R=os.path.abspath(os.path.join(OUTPUT_DIR,'..','..'));out=os.path.join(R,'media','tutorial-en','public','case','promo-final-v06');motion=os.path.join(out,'individual-motion');os.makedirs(motion,exist_ok=True)
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(D.RuntimeSerialNumber),**kw))));assert r['ok'],r;return r['result']
row=next(r for r in WorkbenchService.Settings(D) if r.Name=='Promo Human').Copy();row.Width=1920;row.Height=1080
view=D.Views.ActiveView;vp=view.ActiveViewport;saved=Rhino.DocObjects.ViewportInfo(vp);grid=vp.ConstructionGridVisible;axes=vp.ConstructionAxesVisible;world=vp.WorldAxesVisible;mode=next(m for m in Rhino.Display.DisplayModeDescription.GetDisplayModes() if m.EnglishName=='Rendered')
gid='e6863806-7b87-4140-adf3-3178e35f9500';iid='auto:10';states=[]
def shot(path):
 b=view.CaptureToBitmap(System.Drawing.Size(1920,1080),mode.DisplayAttributes);b.Save(path,ImageFormat.Png if path.endswith('.png') else ImageFormat.Jpeg);b.Dispose()
try:
 WorkbenchService.ApplyCamera(D,row,vp,1920,1080);vp.ConstructionGridVisible=vp.ConstructionAxesVisible=vp.WorldAxesVisible=False;states.append(api('plant_edit_enter',groupId=gid,individualId=iid));shot(os.path.join(out,'individual-before.png'));previous=0
 for i in range(90):
  t=i/89.;e=t*t*(3-2*t);dx=3*(e-previous);previous=e
  result=api('plant_edit_transform',transform=[1,0,0,dx,0,1,0,0,0,0,1,0,0,0,0,1]);iid=result['individualId'];shot(os.path.join(motion,'frame-'+str(i).zfill(3)+'.jpg'))
 states.append(dict(movedId=iid,translation=[3,0,0]));result=api('plant_individual_update',groupId=gid,individualId=iid,custom=True,scale=1.35,mirror=True,assetId='e55d4f7b-0f15-49e9-bddf-dd999c2d79b7');shot(os.path.join(out,'individual-after.png'));states.append(result)
 json.dump(dict(frames=90,states=states,nativeTransforms=True),open(os.path.join(motion,'capture.json'),'w'),indent=2)
finally:
 api('plant_edit_exit');vp.SetViewProjection(saved,True);vp.ConstructionGridVisible=grid;vp.ConstructionAxesVisible=axes;vp.WorldAxesVisible=world;D.Views.Redraw()
print('Captured real isolation, 90 native movement frames, custom scale and mirror. Owned document only.')


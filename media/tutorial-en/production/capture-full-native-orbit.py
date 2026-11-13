import Rhino,System,clr,json,os,math
from System.Drawing.Imaging import ImageFormat
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi,WorkbenchService
D=__rhino_doc__;assert 'material-check-owned.3dm' in D.Path
R=os.path.abspath(os.path.join(OUTPUT_DIR,'..','..'));F=os.path.join(R,'artifacts','promo-final-v06');req=json.load(open(os.path.join(F,'orbit-request.json')));phase=req['phase'];count=req['count'];out=os.path.join(R,'media','tutorial-en','public','case','promo-final-v06',phase);os.makedirs(out,exist_ok=True)
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(D.RuntimeSerialNumber),**kw))));assert r['ok'],r;return r['result']
gid=System.Guid('e6863806-7b87-4140-adf3-3178e35f9500');obj=D.Objects.FindId(gid);hidden=obj.IsHidden;modified=D.Modified
row=next(r for r in WorkbenchService.Settings(D) if r.Name=='Promo Axon').Copy();row.Width=1920;row.Height=1080;row.Mode=next(m.Id for m in Rhino.Display.DisplayModeDescription.GetDisplayModes() if m.EnglishName==('Arctic' if phase=='white-flight' else 'Rendered'));layer=next(l for l in D.Layers if 'Cedar' in l.Name)
assets=['da8e6581-808e-48ca-8e77-f63885689032','bb197acd-2ecf-446f-868e-895d0821e625','378e3072-9af6-4c5d-9d5f-57042e415f0c','cb477ed4-4586-4ad7-907f-c6386d2bfd0c','da8e6581-808e-48ca-8e77-f63885689032'];records=[];last=-1
try:
 if phase=='white-flight':D.Objects.Hide(gid,True)
 for i in range(count):
  t=i/float(count-1);e=t*t*(3-2*t)
  row.Camera.Yaw=(-12+24*e) if phase=='white-flight' else (-6+44*e) if phase=='variation-flight' else 9.84
  row.Camera.Zoom=.95 if phase=='white-flight' else .85 if phase=='variation-flight' else .88
  if phase=='variation-flight':
   ix=min(4,i*5//count);row.PreviewSeason=['summer','autumn','winter','spring','summer'][ix]
   if ix!=last:api('material_apply',assetId=assets[ix],layers=[str(layer.Id)]);records.append(dict(frame=i,asset=assets[ix],season=row.PreviewSeason));last=ix
  if phase=='sun-flight':
   row.Sun.UseDocument=False;row.Sun.Azimuth=120+35*e;row.Sun.Altitude=16+42*e
  bmp=WorkbenchService.Preview(D,row,1920);bmp.Save(os.path.join(out,'frame-'+str(i).zfill(3)+'.jpg'),ImageFormat.Jpeg);bmp.Dispose()
  if i%15==0:json.dump(dict(phase=phase,frame=i,total=count),open(os.path.join(F,'orbit-progress.json'),'w'))
 json.dump(dict(phase=phase,count=count,native=True,interpolation=False,records=records),open(os.path.join(out,'capture.json'),'w'),indent=2)
finally:
 if hidden:D.Objects.Hide(gid,True)
 else:D.Objects.Show(gid,True)
 if phase=='variation-flight':api('material_apply',assetId=assets[0],layers=[str(layer.Id)])
 D.Modified=modified;D.Views.Redraw()
print(json.dumps(dict(phase=phase,frames=count)))

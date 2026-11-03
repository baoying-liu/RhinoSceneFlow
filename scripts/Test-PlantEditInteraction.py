"""B native list/mouse callback regressions. No OS input or library writes."""
import Rhino,System,clr,json,os,traceback
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi,PlantEditing,PlantGroups,PlantService
from System.Reflection import BindingFlags
from Eto.Forms import UITimer,GridCellMouseEventArgs,MouseButtons,Keys
from Eto.Drawing import PointF
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'plant-edit0172');receipt=json.load(open(os.path.join(folder,'backup.json')));assert doc.Path==receipt['backup']
flags=BindingFlags.Static|BindingFlags.Instance|BindingFlags.Public|BindingFlags.NonPublic;root=System.Guid('73fb8208-d869-4935-bb7e-23a6e81e4641')
pg=clr.GetClrType(PlantGroups);pe=clr.GetClrType(PlantEditing);ps=clr.GetClrType(PlantService);key=pg.GetField('Key',flags).GetRawConstantValue();spec=doc.Objects.FindId(root).Attributes.GetUserString(key)
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
api('plant_list_select',groups=[str(root)])
def queue():
 timer=UITimer();timer.Interval=.25;phase=0;cycles=0;started=System.DateTime.UtcNow;result=dict(pid=EXPECTED_PID)
 def capture(name):
  view=doc.Views.ActiveView;b=view.CaptureToBitmap(System.Drawing.Size(1000,750),view.ActiveViewport.DisplayMode.DisplayAttributes);assert b is not None;b.Save(os.path.join(folder,name+'.png'),System.Drawing.Imaging.ImageFormat.Png);b.Dispose()
 def tick(sender,args):
  nonlocal phase,cycles
  try:
   assert (System.DateTime.UtcNow-started).TotalSeconds<90,'Timed out'
   if Rhino.RhinoApp.InCommand>0:return
   ws=api('material_workspace_status');panel=Rhino.UI.Panels.GetPanel(System.Guid(ws['pages'][5]['panelId']));tool=panel.GetType().GetProperty('Tool',flags).GetValue(panel);grid=tool.GetType().GetField('list',flags).GetValue(tool)
   if grid.DataStore is None:return
   if phase==0:
    api('plant_edit_exit');doc.Objects.UnselectAll();capture('before');phase=1
   elif phase==1:
    if cycles:assert api('plant_edit_status')['isolated'],'Deferred list clear unexpectedly exited editing'
    if cycles>=12:phase=2;return
    api('plant_edit_exit');item=list(grid.DataStore)[0]
    ev=GridCellMouseEventArgs(grid.Columns[0],0,0,item,MouseButtons.Primary,System.Enum.ToObject(clr.GetClrType(Keys),0),PointF(4,4),None,0.0)
    grid.GetType().GetMethod('OnCellDoubleClick',flags).Invoke(grid,System.Array[System.Object]([ev]))
    assert api('plant_edit_status')['isolated'];grid.SelectedRows=System.Array[System.Int32]([]);cycles+=1
   elif phase==2:
    assert api('plant_edit_status')['isolated'];capture('isolated');result['repeatedListEntry']=cycles;result['deferredEmptySelectionStable']=True
    view=doc.Views.ActiveView;vp=view.ActiveViewport;camera=ps.GetMethod('Camera',flags).Invoke(None,System.Array[System.Object]([vp]));settings=ps.GetProperty('Settings',flags).GetValue(None)
    picker=pe.GetField('picker',flags).GetValue(None);ctor=clr.GetClrType(Rhino.UI.MouseCallbackEventArgs).GetConstructors(flags)[0];hits={};faint=None
    def callback(x,y,double):
     ev=ctor.Invoke(System.Array[System.Object]([System.UInt32(view.RuntimeSerialNumber),System.UInt32(1),System.Int32(x),System.Int32(y)]))
     picker.GetType().GetMethod('OnMouseDoubleClick' if double else 'OnMouseDown',flags).Invoke(picker,System.Array[System.Object]([ev]));assert ev.Cancel
    for entry in pg.GetMethod('Drawables',flags).Invoke(None,System.Array[System.Object]([doc,doc.Objects.FindId(root)])):
     b=entry.Item2;axes=b.Axes(camera,settings);right=axes.Item1;up=axes.Item2
     for ui in range(2,19,2):
      for vi in range(2,19,2):
       u=ui/20.;v=vi/20.;alpha=b.Image.Sample(u,v).Item4
       if alpha<.02:continue
       du=(1-u if b.Mirror else u)-b.PivotU;dv=v-b.AnchorV;offset=max(b.Width,b.Height)*1e-5
       p=Rhino.Geometry.Point3d(b.Anchor.X+right.X*du*b.Width+up.X*dv*b.Height+camera.Back.X*offset,b.Anchor.Y+right.Y*du*b.Width+up.Y*dv*b.Height+camera.Back.Y*offset,b.Anchor.Z+right.Z*du*b.Width+up.Z*dv*b.Height+camera.Back.Z*offset)
       xy=vp.WorldToClient(p);x=int(round(xy.X));y=int(round(xy.Y))
       if x<0 or y<0 or x>=vp.Size.Width or y>=vp.Size.Height:continue
       hit=PlantEditing.Pick(doc,vp,x,y)
       if hit is None:continue
       if hit.IndividualId not in hits:hits[hit.IndividualId]=[x,y]
       if .02<=alpha<.15 and hit.IndividualId==b.Id.split('/',1)[1]:faint=[x,y,alpha]
    assert len(hits)>=8,('Too few independently pickable plants',hits)
    for row,xy in hits.items():
     api('plant_edit_enter',groupId=str(root));callback(xy[0],xy[1],False);assert api('plant_edit_status')['individual']==row
    result['nativeSingleClicks']=len(hits);result['faintLeafHit']=faint
    blank=next(([x,y] for x,y in [(5,5),(vp.Size.Width-6,5),(5,vp.Size.Height-6)] if PlantEditing.Pick(doc,vp,x,y) is None),None);assert blank is not None
    callback(blank[0],blank[1],True);assert not api('plant_edit_status')['isolated'];result['blankDoubleClickExited']=True
    row,xy=next(iter(hits.items()));callback(xy[0],xy[1],True);assert api('plant_edit_status')['isolated'] and api('plant_edit_status')['individual']==row
    callback(blank[0],blank[1],True);assert not api('plant_edit_status')['isolated'];result['viewportReentryAndBlankExit']=True
    assert doc.Objects.FindId(root).Attributes.GetUserString(key)==spec
    assert not any(o.Attributes.GetUserString('RhinoSceneFlow.PlantEdit.Lock.v1') for o in doc.Objects)
    doc.Objects.UnselectAll();capture('after');result['parametersUnchanged']=True;result['lockMarkersClean']=True;result['modified']=doc.Modified
    timer.Stop();json.dump(result,open(os.path.join(folder,'interaction.json'),'w'),indent=2)
  except Exception:
   timer.Stop();result['error']=traceback.format_exc();result['phase']=phase;json.dump(result,open(os.path.join(folder,'interaction.json'),'w'),indent=2)
 timer.Elapsed+=tick;System.AppDomain.CurrentDomain.SetData('SceneFlowPlantEditInteractionTest',timer);timer.Start()
queue();print('Native interaction regression queued')

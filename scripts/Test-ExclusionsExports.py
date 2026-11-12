"""B-only actual Rhino geometry, asynchronous PSD receipts, cancel and recovery checks.
Uses existing plant assets; no AI calls, user mouse, production installation or publication.
"""
import json,subprocess,sys,time,uuid
from pathlib import Path
from psd_tools import PSDImage

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/exclusions-exports0232';OUT.mkdir(parents=True,exist_ok=True)
HEADER=r'''
import Rhino,System,clr,json,os,math
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi,PlantGroups
from System.Reflection import BindingFlags
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=Rhino.RhinoDoc.ActiveDoc
def rows(obj):return clr.GetClrType(PlantGroups).GetMethod('Rows',BindingFlags.NonPublic|BindingFlags.Static).Invoke(None,System.Array[System.Object]([obj]))
def call(op,**kw):return json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
def api(op,**kw):
    result=call(op,**kw)
    assert result['ok'],result
    return result['result']
folder=os.path.join(OUTPUT_DIR,'exclusions0232');os.makedirs(folder,exist_ok=True)
'''
def run(name,source):
    p=OUT/(name+'.py');p.write_text(HEADER+source,encoding='utf-8')
    result=json.loads(subprocess.check_output([sys.executable,str(ROOT/'scripts/Rhino-Mcp.py'),'run_python',str(p)],encoding='utf-8'))
    text='\n'.join(x.get('text','') for x in result.get('result',{}).get('content',[]))
    (OUT/(name+'.log')).write_text(text,encoding='utf-8')
    for line in text.splitlines():
        if line.startswith('CHECK:'):return json.loads(line[6:])
    raise AssertionError(name+': '+text[-2500:])

setup=run('setup',r'''
if list(doc.Objects):
    previous=json.load(open(os.path.join(folder,'setup.json')))
    own=set(previous[k] for k in ('surface','obstacle','group','mesh','meshGroup'))
    assert set(str(o.Id) for o in doc.Objects)==own and int(doc.RuntimeSerialNumber)==previous['document'],'Never clear user geometry'
    for id in own:assert doc.Objects.Delete(System.Guid(id),True)
    if previous.get('view'):
        index=doc.NamedViews.FindByName('0232 Avoidance PSD')
        if index>=0:doc.NamedViews.Delete(index)
    doc.Modified=False
assert not list(doc.Objects) and not doc.Modified,'Use a fresh empty B document, not a user model'
doc.ModelUnitSystem=Rhino.UnitSystem.Meters
g=Rhino.Geometry
def loop(x0,y0,x1,y1):return g.PolylineCurve([g.Point3d(x0,y0,0),g.Point3d(x1,y0,0),g.Point3d(x1,y1,0),g.Point3d(x0,y1,0),g.Point3d(x0,y0,0)])
outer=loop(0,0,10,10);inner=loop(4,4,6,6)
breps=g.Brep.CreatePlanarBreps(System.Array[g.Curve]([outer,inner]),doc.ModelAbsoluteTolerance)
assert len(breps)==1 and breps[0].Faces[0].Loops.Count==2,'Trimmed hole not created'
carrier=breps[0];carrier.Transform(g.Transform.Rotation(math.radians(12),g.Vector3d.XAxis,g.Point3d.Origin))
surface=doc.Objects.AddBrep(carrier)
box=g.BoundingBox(g.Point3d(1,1,-2),g.Point3d(3,3,8)).ToBrep();obstacle=doc.Objects.AddBrep(box)
assets=api('plant_library')['assets'];assert assets,'Need an existing verified plant asset'
asset=assets[0]['id'];palette=[dict(asset=asset,spacingMeters=.5,weight=1)]
group=api('plant_group_create',spec=dict(name='Trimmed Brep - geometry avoidance',surface=str(surface),palette=palette,settings=dict(density=.45)))['id']
# Add a manual point before defining the obstacle, so the existing conflict must be retained.
api('plant_group_manual',groupId=group,assetId=asset,point=[2,2,0])
state=api('plant_group_state',groupId=group);spec=state['spec'];spec.update(exclusionObjects=[str(obstacle)],exclusionClearanceMeters=.25,exclusionMode='geometry')
api('plant_group_update',groupId=group,spec=spec)
# A separate trimmed Mesh carrier must preserve the same hole.
mesh=g.Mesh()
for part in g.Mesh.CreateFromBrep(carrier,Rhino.Geometry.MeshingParameters.Default):mesh.Append(part);part.Dispose()
mesh.Transform(g.Transform.Translation(14,0,0));meshId=doc.Objects.AddMesh(mesh)
meshGroup=api('plant_group_create',spec=dict(name='Trimmed Mesh',surface=str(meshId),palette=palette,settings=dict(density=.35)))['id']
record=dict(pid=EXPECTED_PID,document=int(doc.RuntimeSerialNumber),surface=str(surface),obstacle=str(obstacle),group=group,mesh=str(meshId),meshGroup=meshGroup,asset=asset)
with open(os.path.join(folder,'setup.json'),'w') as f:json.dump(record,f)
print('CHECK:'+json.dumps(record))
''')
def stable():
    for i in range(80):
        result=run('poll',r'''
s=json.load(open(os.path.join(folder,'setup.json')))
states=[api('plant_group_state',groupId=s[k]) for k in ('group','meshGroup')]
print('CHECK:'+json.dumps(dict(ready=all(not a['busy'] for a in states),errors=[a['error'] for a in states])))
''')
        if result['ready']:
            assert not any(result['errors']),result
            return
        time.sleep(.2)
    raise TimeoutError('Plant layout did not become stable')
stable()
first=run('validate-first',r'''
s=json.load(open(os.path.join(folder,'setup.json')));g=Rhino.Geometry
source=doc.Objects.FindId(System.Guid(s['surface'])).Geometry;obstacle=doc.Objects.FindId(System.Guid(s['obstacle'])).Geometry
state=api('plant_group_state',groupId=s['group']);assert state['count']>20 and state['exclusionConflicts']==1 and state['manual']==1,state
for key,dx in [('group',0),('meshGroup',14)]:
    plants=rows(doc.Objects.FindId(System.Guid(s[key])))
    assert len(plants)>20
    for row in plants:
        p=g.Point3d(row.Position.X-dx,row.Position.Y,row.Position.Z)
        ok,u,v=source.Faces[0].ClosestPoint(p);assert ok and source.Faces[0].IsPointOnFace(u,v)!=g.PointFaceRelation.Exterior,'Plant inside Trim hole'
        if key=='group' and not row.Manual:
            assert not obstacle.IsPointInside(p,1e-6,False)
            assert p.DistanceTo(obstacle.ClosestPoint(p))>=.25-1e-5,'Safety clearance violated'
rejected=call('plant_group_manual',groupId=s['group'],assetId=s['asset'],point=[2,2,0]);assert not rejected['ok'],'Manual placement into obstacle accepted'
spec=state['spec'];bad=dict(spec);bad['exclusionObjects']=[s['surface']]
assert not call('plant_group_update',groupId=s['group'],spec=bad)['ok'],'Carrier accepted as its own obstacle'
# Move the referenced obstacle while keeping its ID. The layout must invalidate itself.
shifted=obstacle.DuplicateBrep();shifted.Transform(g.Transform.Translation(5,0,0));assert doc.Objects.Replace(System.Guid(s['obstacle']),shifted)
print('CHECK:'+json.dumps(dict(trimmedBrep=True,trimmedMesh=True,holePreserved=True,manualConflictPreserved=True,manualRejected=True,count=state['count'])))
''')
stable()
carrier_change=run('move-carrier',r'''
s=json.load(open(os.path.join(folder,'setup.json')));g=Rhino.Geometry
carrier=doc.Objects.FindId(System.Guid(s['surface'])).Geometry.DuplicateBrep();carrier.Transform(g.Transform.Translation(0,0,2));assert doc.Objects.Replace(System.Guid(s['surface']),carrier)
print('CHECK:'+json.dumps(dict(carrierChanged=True)))
''')
stable()
second=run('validate-move-export',r'''
s=json.load(open(os.path.join(folder,'setup.json')));g=Rhino.Geometry
state=api('plant_group_state',groupId=s['group']);assert state['exclusionConflicts']==0,state
obstacle=doc.Objects.FindId(System.Guid(s['obstacle'])).Geometry
for row in rows(doc.Objects.FindId(System.Guid(s['group']))):
    source=doc.Objects.FindId(System.Guid(s['surface'])).Geometry;p=Rhino.Geometry.Point3d(row.Position.X,row.Position.Y,row.Position.Z)
    ok,u,v=source.Faces[0].ClosestPoint(p);assert ok and p.DistanceTo(source.Faces[0].PointAt(u,v))<1e-5,'Carrier edit did not update plant height'
    if not row.Manual:
        p=g.Point3d(row.Position.X,row.Position.Y,row.Position.Z);assert not obstacle.IsPointInside(p,1e-6,False);assert p.DistanceTo(obstacle.ClosestPoint(p))>=.25-1e-5
doc.Views.ActiveView.ActiveViewport.ZoomExtents()
view=api('workbench_create_view',name='0232 Avoidance PSD')['viewId']
api('configure_view',viewId=view,settings=dict(width=256,height=192,layers=[dict(kind='material',blend='norm',opacity=100,enabled=True,visible=True)]))
path=os.path.join(folder,'Avoidance-0232.3dm');opts=Rhino.FileIO.FileWriteOptions();opts.UpdateDocumentPath=True;opts.SuppressDialogBoxes=True;assert doc.WriteFile(path,opts)
saved=next(v for v in api('workbench_settings')['views'] if v['id']==view);assert saved['width']==256 and saved['height']==192,'Save As lost export settings'
before=dict(objects=doc.Objects.Count,modified=doc.Modified)
request=dict(directory=os.path.join(folder,'psd-'+System.Guid.NewGuid().ToString('N')),views=[view],requestId=str(System.Guid.NewGuid()),collision='number')
one=api('export_workbench_start',**request);two=api('export_workbench_start',**request)
assert one['jobId']==two['jobId']==request['requestId']
reordered=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation='export_workbench_start',document=int(doc.RuntimeSerialNumber),**request),sort_keys=True,indent=2)))
assert reordered['ok'] and reordered['result']['jobId']==one['jobId'],'JSON formatting/order broke idempotency'
assert len(one['targets'])==1 and one['targets'][0]['width']==256,'Planned targets must be persisted before writing'
s.update(view=view,request=request,before=before,model=path);json.dump(s,open(os.path.join(folder,'setup.json'),'w'))
print('CHECK:'+json.dumps(dict(obstacleChangeRecomputed=True,model=path,job=one['jobId'],responseStatus=one['status'],receipt=one['receipt'])))
''')
def export_terminal(job):
    for i in range(100):
        result=run('export-poll',"print('CHECK:'+json.dumps(api('export_job_status',jobId="+repr(job)+")))")
        if result['terminal']:return result
        time.sleep(.15)
    raise TimeoutError('Export job not terminal')
exported=export_terminal(second['job']);assert exported['status']=='completed',exported
assert len(exported['files'])==1 and exported['files'][0]['ok']
psd=Path(exported['files'][0]['path']);image=PSDImage.open(psd);assert image.size==(256,192) and len(image)>0
cancel=run('cancel-and-recover',r'''
from System.Reflection import BindingFlags
s=json.load(open(os.path.join(folder,'setup.json')));request=s['request']
same=api('export_workbench_start',**request);assert same['status']=='completed' and len(same['files'])==1
assert len([n for n in os.listdir(request['directory']) if n.endswith('.psd')])==1,'Duplicate PSD written'
changed=dict(request);changed['directory']=os.path.join(folder,'other');assert not call('export_workbench_start',**changed)['ok'],'requestId conflict accepted'
nextRequest=dict(request);nextRequest['requestId']=str(System.Guid.NewGuid())
queued=api('export_workbench_start',**nextRequest);api('export_job_cancel',jobId=queued['jobId'])
assert doc.Objects.Count==s['before']['objects'] and doc.Modified==s['before']['modified'],'Export mutated document'
print('CHECK:'+json.dumps(dict(job=queued['jobId'],duplicateDidNotWrite=True,requestConflictRejected=True,documentPreserved=True)))
''')
cancelled=export_terminal(cancel['job']);assert cancelled['status']=='cancelled' and not cancelled['files'],cancelled
recovery=run('receipt-recovery',r'''
from System.Reflection import BindingFlags
from RhinoSceneFlow.Plugin import ExportJobs
s=json.load(open(os.path.join(folder,'setup.json')));id=System.Guid(s['request']['requestId'])
# Drop the finished in-memory entry; query the actual durable file instead.
jobs=clr.GetClrType(ExportJobs).GetField('jobs',BindingFlags.NonPublic|BindingFlags.Static).GetValue(None)
assert jobs.Remove(id);restored=api('export_job_status',jobId=str(id));assert restored['status']=='completed' and len(restored['files'])==1
new=System.Guid.NewGuid();record=dict(restored);record.update(jobId=str(new),status='writing',terminal=False)
path=os.path.join(os.path.dirname(restored['receipt']),new.ToString('N')+'.json');json.dump(record,open(path,'w'))
interrupted=api('export_job_status',jobId=str(new));assert interrupted['status']=='interrupted' and interrupted['terminal'] and len(interrupted['files'])==1
print('CHECK:'+json.dumps(dict(durableReadback=True,interruptedNotRestarted=True,model=s['model'])))
''')
receipt=dict(version='0.23.2',pid=setup['pid'],geometry=first,carrier=carrier_change,moved=second,export=exported,cancel=cancel,recovery=recovery,realPsdParsed=True,modelCalls=0)
(OUT/'verified.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8');print(json.dumps(receipt,indent=2))

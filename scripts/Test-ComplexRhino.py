"""Create actual NURBS/Brep tests in a fresh sandbox B document and export without UI input."""
import json, math, os, time
import clr, System, Rhino
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
from Rhino.Geometry import (Point3d, Vector3d, Plane, Circle, Sphere, Torus, Brep, Mesh,
    NurbsSurface, BoundingBox, Transform, LineCurve, Line)
from Rhino.Geometry.Intersect import Intersection
from Rhino.DocObjects import Layer, ObjectAttributes
from Rhino.Display import DefinedViewportProjection, DisplayModeDescription, ViewCapture
from System.Drawing import Color

assert System.Diagnostics.Process.GetCurrentProcess().Id == EXPECTED_PID
doc = __rhino_doc__
existing=list(doc.Objects)
if existing:
    assert all(o.Attributes.GetUserString('SceneFlowComplexTest')=='v1' or
        (len(existing)==2 and o.Attributes.Name=='Sphere' and doc.Layers[o.Attributes.LayerIndex].FullPath=='Complex_Sphere')
        for o in existing), 'Existing non-test geometry must not be replaced'
    for o in existing: assert doc.Objects.Delete(o,True)
folder = os.path.join(OUTPUT_DIR, 'complex')
os.makedirs(folder, exist_ok=True)
stamp = str(System.Guid.NewGuid()).split('-')[0]
references = []
objects = []
colors = {}

def layer(name, rgb):
    item = Layer(); item.Name = 'Complex_' + name; item.Color = Color.FromArgb(*rgb)
    colors[name] = list(rgb)
    found=doc.Layers.FindByFullPath(item.Name,-1)
    if found>=0:return found
    return doc.Layers.Add(item)

def add(name, geometry, rgb, reference=None, layer_index=None):
    index = layer_index if layer_index is not None else layer(name, rgb)
    attributes = ObjectAttributes(); attributes.LayerIndex = index; attributes.Name = name
    attributes.SetUserString('SceneFlowComplexTest','v1')
    if isinstance(geometry, Brep):
        object_id = doc.Objects.AddBrep(geometry, attributes)
        oracle = geometry
    elif isinstance(geometry, Mesh):
        object_id = doc.Objects.AddMesh(geometry, attributes)
        oracle = reference
    else:
        object_id = doc.Objects.AddSurface(geometry, attributes)
        oracle = geometry.ToBrep()
    assert object_id != System.Guid.Empty and oracle.IsValid, name
    references.append((name, oracle))
    objects.append({'name':name,'id':str(object_id),'kind':str(doc.Objects.FindId(object_id).ObjectType)})
    return index

red = (220,65,45)
sphere_layer = add('Sphere', Sphere(Point3d(-6,0,3),3).ToBrep(), red)
add('Sphere', Sphere(Point3d(-6,0,6.5),1.5).ToBrep(), red, layer_index=sphere_layer)
saddle = Brep.CreateFromCornerPoints(Point3d(0,-3,5.5),Point3d(6,-3,.5),
    Point3d(6,3,5.5),Point3d(0,3,.5),doc.ModelAbsoluteTolerance)
add('Saddle', saddle.Surfaces[0].ToNurbsSurface(), (45,120,210))

# Equal circles with 120-degree parameter phase produce an exact ruled one-sheet hyperboloid.
c0 = Circle(Plane(Point3d(11,0,0),Vector3d.ZAxis),3).ToNurbsCurve()
c1 = Circle(Plane(Point3d(11,0,7),Vector3d.ZAxis),3).ToNurbsCurve()
c1.Transform(Transform.Rotation(2*math.pi/3, Vector3d.ZAxis, Point3d(11,0,7)))
hyperboloid = NurbsSurface.CreateRuledSurface(c0,c1)
middle = hyperboloid.PointAt(hyperboloid.Domain(0).Mid,hyperboloid.Domain(1).Mid)
waist = math.hypot(middle.X-11,middle.Y)
assert abs(waist-1.5)<1e-8, ('Incorrect hyperboloid waist',waist)
add('Hyperboloid',hyperboloid,(45,165,100))
add('Torus',Torus(Plane(Point3d(20,0,2),Vector3d.ZAxis),3,1).ToBrep(),(240,175,35))
curves = System.Array[Rhino.Geometry.Curve]([
    Circle(Plane(Point3d(29,0,3),Vector3d.ZAxis),3).ToNurbsCurve(),
    Circle(Plane(Point3d(29,0,3),Vector3d.ZAxis),1.4).ToNurbsCurve()])
annulus = Brep.CreatePlanarBreps(curves,doc.ModelAbsoluteTolerance)
assert len(annulus)==1 and annulus[0].Loops.Count==2
add('TrimmedAnnulus',annulus[0],(155,80,200))
ground = Mesh()
corners=[Point3d(-11,-7,-2),Point3d(34,-7,-2),Point3d(34,7,-2),Point3d(-11,7,-2)]
for p in corners: ground.Vertices.Add(p)
ground.Faces.AddFace(0,1,2,3)
ground.Normals.ComputeNormals()
add('Ground',ground,(185,190,195),reference=Brep.CreateFromCornerPoints(*corners,doc.ModelAbsoluteTolerance))

def api(operation, **kwargs):
    return json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=operation,
        document=int(doc.RuntimeSerialNumber),**kwargs))))
view=doc.Views.ActiveView; vp=view.ActiveViewport
vp.DisplayMode=DisplayModeDescription.FindByName('Shaded')
bounds=BoundingBox(Point3d(-11,-7,-2),Point3d(34,7,8))
report={'pid':EXPECTED_PID,'objects':objects,'colors':colors,'waistRadius':waist,'cases':[]}
report['pluginVersion']=api('describe')['result']['version']
assert report['pluginVersion']=='0.2.1',report['pluginVersion']

def snapshot():
    return (doc.Modified,doc.Objects.Count,tuple(str(o.Id) for o in doc.Objects.GetSelectedObjects(False,False)),
        str(vp.DisplayMode.Id),str(vp.CameraLocation),str(vp.CameraDirection),
        tuple((str(l.Id),l.Color.ToArgb(),l.IsVisible,l.IsLocked) for l in doc.Layers if not l.IsDeleted))

def oracle(px,py,width,height):
    ok,line=vp.GetFrustumLine(px*vp.Size.Width/width,py*vp.Size.Height/height)
    assert ok
    # This installed Rhino build returns far-to-near in parallel views; orient explicitly.
    if line.From.DistanceTo(vp.CameraLocation)>line.To.DistanceTo(vp.CameraLocation):line=Line(line.To,line.From)
    curve=LineCurve(line)
    closest=float('inf'); name=None
    try:
        for label,geometry,rect in screened:
            if not (rect[0]-2<=px<=rect[2]+2 and rect[1]-2<=py<=rect[3]+2):continue
            # Unlike RayShoot, CurveBrep respects trimming loops, including actual holes.
            ok,parameters=Intersection.CurveBrep(curve,geometry,1e-6,1e-6)
            if parameters:
                for parameter in parameters:
                    distance=line.From.DistanceTo(curve.PointAt(parameter))
                    if distance<closest:closest=distance;name=label
    finally:curve.Dispose()
    return name

for name,camera in [('top',None),('perspective',(45,-48,36)),('low-angle',(-30,-40,15)),('detail-2048',(-30,-40,15))]:
    if camera is None:
        vp.SetProjection(DefinedViewportProjection.Top,'Complex_Top',True)
    else:
        vp.SetProjection(DefinedViewportProjection.Perspective,'Complex_'+name,True)
        vp.SetCameraLocations(Point3d(11,0,2),Point3d(*camera))
    vp.ZoomBoundingBox(bounds)
    vp.DisplayMode=DisplayModeDescription.FindByName('Shaded')
    doc.Views.Redraw()
    export_path=os.path.join(os.path.dirname(OUTPUT_DIR),'exports','complex-'+stamp+'-'+name+'.psd')
    before=snapshot()
    result=api('export_psd',width=2048 if name=='detail-2048' else 1024,path=export_path,viewportId=str(vp.Id))
    assert result['ok'],result
    assert snapshot()==before,'Export modified scene'
    data=result['result']; width=data['width']; height=data['height']
    screened=[]
    for label,geometry in references:
        pixels=[vp.WorldToClient(p) for p in geometry.GetBoundingBox(True).GetCorners()]
        rect=(min(p.X for p in pixels)*width/vp.Size.Width,min(p.Y for p in pixels)*height/vp.Size.Height,
              max(p.X for p in pixels)*width/vp.Size.Width,max(p.Y for p in pixels)*height/vp.Size.Height)
        screened.append((label,geometry,rect))
    samples=[]; started=time.time()
    # Check against Rhino's exact NURBS/Brep ray intersections, not our rasterizer or render meshes.
    for gy in range(18):
        for gx in range(48):
            x=int((gx+.5)*width/48); y=int((gy+.5)*height/18)
            expected=oracle(x+.5,y+.5,width,height)
            if all(oracle(x+.5+dx,y+.5+dy,width,height)==expected for dx,dy in [(1.5,0),(-1.5,0),(0,1.5),(0,-1.5)]):
                samples.append({'x':x,'y':y,'expected':expected})
    capture=ViewCapture(); capture.Width=width; capture.Height=height
    capture.DrawAxes=False; capture.DrawGrid=False; capture.DrawGridAxes=False
    bitmap=capture.CaptureToBitmap(view)
    if bitmap:
        bitmap.Save(os.path.join(folder,name+'-viewport.png'));bitmap.Dispose()
    case={'name':name,'export':data,'samples':samples,'oracleSeconds':time.time()-started,
        'stateUnchanged':True}
    if name=='top':
        center=vp.WorldToClient(Point3d(-6,0,3));edge=vp.WorldToClient(Point3d(-3,0,3))
        case['sphereCircle']={'x':center.X*width/vp.Size.Width,'y':center.Y*height/vp.Size.Height,
            'radius':abs(edge.X-center.X)*width/vp.Size.Width}
        holes=[]
        for label,p in [('Torus',Point3d(20,0,-2)),('TrimmedAnnulus',Point3d(29,0,-2)),('Hyperboloid',Point3d(11,0,-2))]:
            screen=vp.WorldToClient(p)
            holes.append({'name':label,'x':int(screen.X*width/vp.Size.Width),'y':int(screen.Y*height/vp.Size.Height)})
        case['holes']=holes
    report['cases'].append(case)
    with open(os.path.join(folder,'report.json'),'w') as handle: json.dump(report,handle,indent=2)

options=Rhino.FileIO.FileWriteOptions();options.SuppressDialogBoxes=True
doc.WriteFile(os.path.join(folder,'Complex-Surfaces.3dm'),options)
report['complete']=True
with open(os.path.join(folder,'report.json'),'w') as handle:json.dump(report,handle,indent=2)
print(json.dumps({'complete':True,'report':os.path.join(folder,'report.json'),
    'cases':[{k:c['export'][k] for k in ['path','layerCount','triangles','elapsedMilliseconds']} for c in report['cases']]}))

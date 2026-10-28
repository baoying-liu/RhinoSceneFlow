"""B-only async native xatlas test; retain owned complex fixtures for inspection."""
import Rhino,System,clr,json,os,math,time
from Rhino.Geometry import Mesh,Point3d,Vector3d,Sphere,BoundingBox
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'xatlas');os.makedirs(folder,exist_ok=True)
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))));assert r['ok'],r;return r['result']
scale=Rhino.RhinoMath.UnitScale(Rhino.UnitSystem.Meters,doc.ModelUnitSystem)
tag='Xatlas_'+str(System.Guid.NewGuid())[:8]
l=Rhino.DocObjects.Layer();l.Name=tag;li=doc.Layers.Add(l);ids=[]
def add(name,g):
 a=Rhino.DocObjects.ObjectAttributes();a.Name=name;a.LayerIndex=li;a.SetUserString('SceneFlow.XatlasTest',tag)
 id=doc.Objects.Add(g,a);ids.append(str(id));return id
def center(t):return Point3d(3*math.sin(t)+6*math.sin(2*t),3*math.cos(t)-6*math.cos(2*t),-3*math.sin(3*t))
n=600;m=64;mesh=Mesh()
for i in range(n):
 t=i*2*math.pi/n;c=center(t);tangent=center(t+.0001)-center(t-.0001);tangent.Unitize();a=Vector3d.CrossProduct(tangent,Vector3d.ZAxis);a.Unitize();b=Vector3d.CrossProduct(tangent,a);b.Unitize()
 for j in range(m):
  q=j*2*math.pi/m;p=c+.7*math.cos(q)*a+.7*math.sin(q)*b;mesh.Vertices.Add((100+p.X)*scale,(100+p.Y)*scale,(5+p.Z)*scale)
for i in range(n):
 for j in range(m):
  a0=i*m+j;b0=((i+1)%n)*m+j;c0=((i+1)%n)*m+(j+1)%m;d0=i*m+(j+1)%m
  mesh.Faces.AddFace(a0,c0,b0);mesh.Faces.AddFace(a0,d0,c0)
mesh.Normals.ComputeNormals();assert mesh.IsValid
# Closed tube faces must point outward before UV / material validation.
volume=Rhino.Geometry.VolumeMassProperties.Compute(mesh);assert volume is not None and volume.Volume>0;volume.Dispose()
assert mesh.SolidOrientation()==1
knot=add('Trefoil knot 76800 triangles',mesh);mesh.Dispose()
sphere=Sphere(Point3d(112*scale,100*scale,2*scale),2*scale).ToBrep();add('NURBS Sphere',sphere);sphere.Dispose()
source=[dict(id=id,crc=int(doc.Objects.FindId(System.Guid(id)).Geometry.DataCRC(0)),type=doc.Objects.FindId(System.Guid(id)).Geometry.GetType().Name) for id in ids]
job=api('material_unwrap_start',objects=ids)
report=dict(pid=EXPECTED_PID,document=int(doc.RuntimeSerialNumber),tag=tag,layer=str(doc.Layers[li].Id),objects=source,job=job,started=time.time(),unitsPerMeter=scale)
with open(os.path.join(folder,'start.json'),'w') as f:json.dump(report,f,indent=2)
print(json.dumps(job))

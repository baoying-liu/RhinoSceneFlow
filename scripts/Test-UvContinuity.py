import Rhino,System,clr,json,os,math
from Rhino.Geometry import Mesh,PolylineCurve,Point3d,Sphere
from System.Drawing import Bitmap,Color
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'uv-v012');os.makedirs(folder,exist_ok=True)
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))));assert r['ok'],r;return r['result']
scale=Rhino.RhinoMath.UnitScale(Rhino.UnitSystem.Meters,doc.ModelUnitSystem)
src=Mesh();rings=600;sides=64
for i in range(rings):
 t=2*math.pi*i/rings
 def c(t):return Point3d(3*math.sin(t)+6*math.sin(2*t),3*math.cos(t)-6*math.cos(2*t),-3*math.sin(3*t))
 p=c(t);tangent=c(t+.0001)-c(t-.0001);tangent.Unitize();a=Rhino.Geometry.Vector3d.CrossProduct(tangent,Rhino.Geometry.Vector3d.ZAxis);a.Unitize();b=Rhino.Geometry.Vector3d.CrossProduct(tangent,a);b.Unitize()
 for j in range(sides):
  q=2*math.pi*j/sides;v=p+a*(.7*math.cos(q))+b*(.7*math.sin(q));src.Vertices.Add((100+v.X)*scale,(100+v.Y)*scale,(5+v.Z)*scale)
for i in range(rings):
 for j in range(sides):
  a=i*sides+j;b=((i+1)%rings)*sides+j;c=((i+1)%rings)*sides+(j+1)%sides;d=i*sides+(j+1)%sides
  src.Faces.AddFace(a,b,c);src.Faces.AddFace(a,c,d)
src.Normals.ComputeNormals();assert src.IsClosed and src.SolidOrientation()==-1
li=Rhino.DocObjects.Layer();li.Name='UV_v012_'+str(System.Guid.NewGuid())[:8];index=doc.Layers.Add(li)
def add(name,g):
 a=Rhino.DocObjects.ObjectAttributes();a.Name=name;a.LayerIndex=index;a.SetUserString('SceneFlow.Uv012Test','owned');id=doc.Objects.Add(g,a);return str(id)
first=add('Inward source - xatlas provider',src)
secondMesh=src.DuplicateMesh();secondMesh.Transform(Rhino.Geometry.Transform.Translation(30*scale,0,0));second=add('Tube continuous UV',secondMesh);secondMesh.Dispose();src.Dispose()
sphere=Sphere(Point3d(112*scale,100*scale,2*scale),2*scale).ToBrep();third=add('NURBS sphere - provider',sphere);sphere.Dispose()
def center(t):return Point3d((130+3*math.sin(t)+6*math.sin(2*t))*scale,(100+3*math.cos(t)-6*math.cos(2*t))*scale,(5-3*math.sin(3*t))*scale)
path=[center(i*2*math.pi/1200) for i in range(1201)];guide=PolylineCurve(path);gid=add('Tube guide',guide);guide.Dispose()
image=Bitmap(512,512)
from System.Drawing import Graphics,SolidBrush,Rectangle
g=Graphics.FromImage(image);g.Clear(Color.FromArgb(215,208,190))
for y in range(4):
 for x in range(-1,3):
  brush=SolidBrush(Color.FromArgb(155+((x+y)%4)*4,65,42));g.FillRectangle(brush,Rectangle(x*256+(128 if y%2 else 0)+7,y*128+7,249,121));brush.Dispose()
g.Dispose()
texture=os.path.join(folder,'metric-brick.png');image.Save(texture);image.Dispose()
asset=api('material_import',asset=dict(name='Brick 1m x 1m - UV regression',widthMeters=1,heightMeters=1),files=dict(baseColor=texture))
job=api('material_unwrap_start',objects=[first,third]);state=dict(pid=EXPECTED_PID,ids=[first,second,third],guide=gid,job=job,asset=asset['id'],scale=scale,crc=[int(doc.Objects.FindId(System.Guid(id)).Geometry.DataCRC(0)) for id in [first,second,third]])
with open(os.path.join(folder,'start.json'),'w') as f:json.dump(state,f,indent=2)
print(json.dumps(state))

"""Build only owned empty B geometry; all assets/UV/planting use SceneFlow APIs."""
import Rhino,System,clr,json,os,math
from Rhino.Geometry import Point3d as P,Vector3d as V,Mesh,Brep,Box,Plane,Interval
from System.Drawing import Color
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;assert doc.Objects.Count==0 and not doc.Modified,'Requires empty B model; preserves existing work.'
doc.ModelUnitSystem=Rhino.UnitSystem.Meters;doc.ModelAbsoluteTolerance=.001
folder=os.path.abspath(os.path.join(OUTPUT_DIR,'..','examples','Hillside-Retreat'));os.makedirs(folder,exist_ok=True)
layers={};objects={};materialsets={}
def layer(name,rgb):
 l=Rhino.DocObjects.Layer();l.Name=name;l.Color=Color.FromArgb(*rgb);i=doc.Layers.Add(l);layers[name]=str(doc.Layers[i].Id);return i
def add(name,g,li,mat=None):
 a=Rhino.DocObjects.ObjectAttributes();a.Name=name;a.LayerIndex=li;a.SetUserString('SceneFlow.Demo','HillsideRetreat.v1')
 oid=doc.Objects.Add(g,a);assert oid!=System.Guid.Empty,name;objects[name]=str(oid)
 if mat:materialsets.setdefault(mat,[]).append(str(oid))
 g.Dispose();return oid
def face(name,pts,li,mat):
 m=Mesh()
 for p in pts:m.Vertices.Add(P(*p))
 for i in range(1,len(pts)-1):m.Faces.AddFace(0,i,i+1)
 m.Normals.ComputeNormals();return add(name,m,li,mat)
def box(name,x0,x1,y0,y1,z0,z1,li,mat):return add(name,Box(Plane.WorldXY,Interval(x0,x1),Interval(y0,y1),Interval(z0,z1)).ToBrep(),li,mat)
grass=layer('01 Site - Meadow',(145,157,109));earth=layer('02 Site - Cut Edge',(92,98,72));paths=layer('03 Site - Paths',(131,132,123));contours=layer('04 Site - Contours',(235,230,202));timber=layer('05 Architecture - Cedar',(136,115,94));plaster=layer('06 Architecture - Plaster',(221,218,202));roof=layer('07 Architecture - Roof',(231,231,224));glass=layer('08 Architecture - Glazing',(94,115,121));frames=layer('09 Architecture - Frames',(48,55,55));deck=layer('10 Architecture - Deck',(154,135,110));planting=layer('11 Planting - Editable Region',(138,154,111))
def h(x,y):
 raw=.75+.043*(y+18)+1.5*math.exp(-((x-13)**2+(y-12)**2)/180)+.48*math.sin(x*.15)*math.cos(y*.14)
 # Graded building pad with a smooth transition into a genuinely rolling site.
 dx=max(-9-x,0,x-10);dy=max(-6-y,0,y-13);d=math.sqrt(dx*dx+dy*dy);t=min(1,d/4);t=t*t*(3-2*t)
 return 1.65*(1-t)+raw*t
nx,ny=80,68;terrain=Mesh();region=Mesh()
for j in range(ny+1):
 y=-18+40.0*j/ny
 for i in range(nx+1):
  x=-24+48.0*i/nx;terrain.Vertices.Add(x,y,h(x,y));region.Vertices.Add(x,y,h(x,y))
for j in range(ny):
 for i in range(nx):
  a=j*(nx+1)+i;terrain.Faces.AddFace(a,a+1,a+nx+2,a+nx+1)
  x=-24+48.0*(i+.5)/nx;y=-18+40.0*(j+.5)/ny
  # Keep vegetation away from architecture and the entrance corridor.
  if not (-12<x<13 and -9<y<16) and not(abs(x-(.22*y-4))<2 and y<-5):region.Faces.AddFace(a,a+1,a+nx+2,a+nx+1)
terrain.Normals.ComputeNormals();terrain.Compact();region.Vertices.CullUnused();region.Normals.ComputeNormals();region.Compact()
inner=terrain.DuplicateMesh();remove=[]
for fi in range(inner.Faces.Count):
 c=inner.Faces.GetFaceCenter(fi);x=c.X;y=c.Y
 if not (-12<x<13 and -9<y<16) and not(abs(x-(.22*y-4))<2 and y<-5):remove.append(fi)
inner.Faces.DeleteFaces(remove);inner.Vertices.CullUnused();inner.Compact()
surface=str(add('Editable rolling meadow',inner,grass,'grass'))
regionId=str(add('Editable planting carrier - excluded building pad',region,planting,'grass'))
# The two meadow meshes partition the site: no duplicate overlapping ground/shadow receiver.
for side,(x0,y0,x1,y1) in enumerate([(-24,-18,24,-18),(24,-18,24,22),(24,22,-24,22),(-24,22,-24,-18)]):
 m=Mesh();n=80
 for i in range(n+1):
  t=i/float(n);x=x0+(x1-x0)*t;y=y0+(y1-y0)*t;m.Vertices.Add(x,y,-.7);m.Vertices.Add(x,y,h(x,y))
 for i in range(n):a=2*i;m.Faces.AddFace(a,a+2,a+3,a+1)
 m.Normals.ComputeNormals();add('Terrain cut edge '+str(side+1),m,earth,'earth')
def ribbon(name,points,width,li,mat,drape=True):
 m=Mesh()
 for i,p in enumerate(points):
  prev=points[max(0,i-1)];nxt=points[min(len(points)-1,i+1)];dx=nxt[0]-prev[0];dy=nxt[1]-prev[1];d=max(.001,math.hypot(dx,dy));ox=-dy/d*width/2;oy=dx/d*width/2
  for s in [-1,1]:
   x=p[0]+s*ox;y=p[1]+s*oy;z=h(x,y)+.035 if drape else p[2]+.045;m.Vertices.Add(x,y,z)
 for i in range(len(points)-1):a=2*i;m.Faces.AddFace(a,a+2,a+3,a+1)
 m.Normals.ComputeNormals();add(name,m,li,mat)
points=[]
for i in range(81):
 y=-18+15.0*i/80;x=-3.8+1.4*math.sin((y+18)*.31);points.append((x,y,0))
ribbon('Curving arrival walk',points,1.65,paths,'gravel')
points=[(7+9*t,2+5*t+1.1*math.sin(t*math.pi),0) for t in [i/60.0 for i in range(61)]];ribbon('Garden walk',points,1.25,paths,'gravel')
for level in [.8+i*.45 for i in range(9)]:
 lines=Rhino.Geometry.Intersect.Intersection.MeshPlane(terrain,Plane(P(0,0,level),V.ZAxis))
 if lines:
  for n,line in enumerate(lines):
   if line.Length>3:ribbon('Contour %.2f %d'%(level,n),[(p.X,p.Y,p.Z) for p in line],.055,contours,'contours',False)
terrain.Dispose()
z=1.78
def gable(prefix,x0,x1,y0,y1,eave,ridge):
 mid=(x0+x1)/2
 box(prefix+' lower walls',x0,x1,y0,y1,z,z+3.1,timber,'cedar')
 box(prefix+' upper walls',x0,x1,y0,y1,z+3.1,eave,plaster,'plaster')
 for y,tag in [(y0,'front'),(y1,'rear')]:face(prefix+' '+tag+' gable',[(x0,y,eave),(x1,y,eave),(mid,y,ridge)],plaster,'plaster')
 face(prefix+' west roof',[(x0-.3,y0-.35,eave+.09),(mid,y0-.35,ridge+.09),(mid,y1+.35,ridge+.09),(x0-.3,y1+.35,eave+.09)],roof,'roof')
 face(prefix+' east roof',[(mid,y0-.35,ridge+.09),(x1+.3,y0-.35,eave+.09),(x1+.3,y1+.35,eave+.09),(mid,y1+.35,ridge+.09)],roof,'roof')
 # Opaque architectural glazing proxies remain compatible with the unlit texture pass.
 yy=y0-.045
 face(prefix+' full height front glazing',[(x0+.4,yy,z+3.5),(x1-.4,yy,z+3.5),(x1-.4,yy,eave-.2),(mid,yy,ridge-.35),(x0+.4,yy,eave-.2)],glass,'glass')
 for i in range(6):
  x=x0+.4+(x1-x0-.8)*i/5;top=eave-.2+(ridge-eave)*max(0,1-abs(x-mid)/((x1-x0)/2))-.12
  box(prefix+' front mullion '+str(i),x-.045,x+.045,yy-.06,yy,z+3.45,top,frames,'frames')
 box(prefix+' transom',x0+.35,x1-.35,yy-.055,yy,z+3.43,z+3.53,frames,'frames')
 for i in range(3):
  y=y0+1.1+i*(y1-y0-2.2)/2
  face(prefix+' side window '+str(i),[(x1+.03,y,z+1.0),(x1+.03,y+1.1,z+1.0),(x1+.03,y+1.1,z+2.05),(x1+.03,y,z+2.05)],glass,'glass')
 box(prefix+' entrance',mid-.55,mid+.55,y0-.04,y0-.01,z,z+2.4,frames,'frames')
gable('West pavilion',-8,-1,-2,8,7.5,10)
gable('Front pavilion',-.3,6.7,-5,3.8,5.9,8.1)
box('North tower cedar base',2,9,5,12,z,z+3,timber,'cedar')
face('North tower west wall',[(2,5,z+3),(2,12,z+3),(2,12,11),(2,5,9.4)],plaster,'plaster')
face('North tower east wall',[(9,12,z+3),(9,5,z+3),(9,5,9.4),(9,12,11)],plaster,'plaster')
face('North tower front wall',[(2,5,z+3),(9,5,z+3),(9,5,9.4),(2,5,9.4)],plaster,'plaster')
face('North tower rear wall',[(9,12,z+3),(2,12,z+3),(2,12,11),(9,12,11)],plaster,'plaster')
face('North tower roof',[(1.7,4.7,9.42),(9.3,4.7,9.42),(9.3,12.3,11.1),(1.7,12.3,11.1)],roof,'roof')
face('North tower east glazing',[(9.04,6,5.2),(9.04,11,5.2),(9.04,11,10.45),(9.04,6,9.3)],glass,'glass')
for i in range(6):
 y=6+i;box('Tower mullion '+str(i),9.04,9.13,y-.045,y+.045,5.15,9.3+(y-6)*.23,frames,'frames')
box('Arrival deck',-9,7.3,-6.4,-5.1,1.66,1.8,deck,'cedar')
box('West entrance landing',-8.6,-.6,-3.6,-2.1,1.66,1.8,deck,'cedar')
for i in range(3):box('Garden bench '+str(i),11+i*2.5,12.8+i*2.5,4.0,4.6,h(12+i*2.5,4)+.1,h(12+i*2.5,4)+.55,deck,'cedar')
vp=doc.Views.ActiveView.ActiveViewport;vp.SetProjection(Rhino.Display.DefinedViewportProjection.Perspective,'Hillside Retreat',True)
vp.SetCameraLocations(P(0,2,2),P(58,-75,57));vp.ChangeToParallelProjection(True)
vp.ZoomBoundingBox(Rhino.Geometry.BoundingBox(P(-26,-20,-1),P(26,24,15)))
vp.ConstructionGridVisible=False;vp.ConstructionAxesVisible=False;vp.WorldAxesIconVisible=False
vp.DisplayMode=Rhino.Display.DisplayModeDescription.GetDisplayMode(Rhino.Display.DisplayModeDescription.RenderedId)
doc.Views.Redraw()
data=dict(folder=folder,surface=surface,carrier=regionId,objects=objects,layers=layers,materialsets=materialsets,document=int(doc.RuntimeSerialNumber))
with open(os.path.join(folder,'geometry.json'),'w') as f:json.dump(data,f,indent=2)
print(json.dumps(dict(objects=len(objects),terrain=surface,carrier=regionId,materialGroups={k:len(v) for k,v in materialsets.items()})))

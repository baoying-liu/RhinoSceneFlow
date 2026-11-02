"""B-only semantic mapping fingerprint oracle, no document edits."""
import Rhino,System,clr,json
from System.Reflection import BindingFlags
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
typ=clr.GetClrType(McpApi).Assembly.GetType('RhinoSceneFlow.Plugin.MappingSnapshot');method=typ.GetMethod('Fingerprint',BindingFlags.Public|BindingFlags.Static)
def fingerprint(mapping):return str(method.Invoke(None,System.Array[System.Object]([mapping])))
def mapping(u=1):
 m=Rhino.Geometry.Mesh()
 for x,y in [(0,0),(1,0),(0,1)]:m.Vertices.Add(x,y,0)
 m.Faces.AddFace(0,1,2)
 for x,y in [(0,0),(u,0),(0,1)]:m.TextureCoordinates.Add(x,y)
 m.Normals.ComputeNormals();result=Rhino.Render.TextureMapping.CreateCustomMeshMapping(m);m.Dispose();return result
a=mapping();b=mapping();c=mapping(1.1)
try:
 assert fingerprint(a)==fingerprint(b),'Same numeric map, different native object identity.'
 assert fingerprint(a)!=fingerprint(c),'UV modification must be detected.'
 before=fingerprint(b);b.UvwTransform=Rhino.Geometry.Transform.Translation(.1,0,0);assert before!=fingerprint(b)
 print(json.dumps(dict(equalIndependentMaps=True,detectsUvEdit=True,detectsTransformEdit=True)))
finally:a.Dispose();b.Dispose();c.Dispose()

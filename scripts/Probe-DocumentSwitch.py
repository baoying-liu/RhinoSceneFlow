"""B-only crash evidence + owned open/new fixture; never suppress exceptions."""
import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin');clr.AddReference('WindowsBase')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
folder=os.path.join(OUTPUT_DIR,'document-switch');os.makedirs(folder,exist_ok=True)
doc=__rhino_doc__
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,**kw))))
 assert r['ok'],r
 return r['result']
def record(message):
 with open(os.path.join(folder,'events-'+str(EXPECTED_PID)+'.log'),'a') as f:f.write(str(System.DateTime.UtcNow)+' '+str(message)+'\n')
def exception(sender,e):record(e.Exception.ToString())
System.Windows.Threading.Dispatcher.CurrentDispatcher.UnhandledException+=exception
def unhandled(sender,e):record(str(e.ExceptionObject))
System.AppDomain.CurrentDomain.UnhandledException+=unhandled
def event(sender,e):record(str(e.Document.RuntimeSerialNumber))
Rhino.RhinoDoc.CloseDocument+=event;Rhino.RhinoDoc.NewDocument+=event;Rhino.RhinoDoc.EndOpenDocument+=event
System.AppDomain.CurrentDomain.SetData('SceneFlowDocumentProbe',[exception,unhandled,event])
fixture=os.path.join(folder,'owned-open.3dm')
if not os.path.exists(fixture):
 model=Rhino.FileIO.File3dm();sphere=Rhino.Geometry.Sphere(Rhino.Geometry.Point3d.Origin,100).ToBrep();model.Objects.AddBrep(sphere);sphere.Dispose();assert model.Write(fixture,8);model.Dispose()
api('material_workspace_open',page='library')
assets=api('material_library')['assets']
if assets:api('material_tool_select',page='library',assetId=assets[-1]['id'])
assert doc.Objects.Count==0,'Fresh B document required; do not replace user content'
record('ready library '+str(doc.RuntimeSerialNumber))
print(json.dumps(dict(pid=EXPECTED_PID,document=int(doc.RuntimeSerialNumber),fixture=fixture,workspace=api('material_workspace_status'))))

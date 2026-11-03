"""Native Open lifecycle check from our fresh empty B document only."""
import Rhino,System,os
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;assert doc.Objects.Count==0 and not doc.Modified and doc.Path is None
path=os.path.join(os.environ['LOCALAPPDATA'],'RhinoSceneFlow','Demos','HillsideRetreat','SceneFlow-Hillside-Retreat-PlantOutline-Fixed.3dm')
assert os.path.isfile(path)
assert Rhino.RhinoApp.RunScript('_-Open "'+path+'" _Enter',False)
print('Opened saved demo read-only for Web tool lifecycle verification')

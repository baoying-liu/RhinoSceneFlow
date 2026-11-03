"""Native New only on the owned regression fixture; restore the pre-test library preference."""
import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'properties017');record=json.load(open(os.path.join(folder,'setup.json')))
assert doc.Path==record['model'],'Do not discard user documents'
oldSerial=int(doc.RuntimeSerialNumber)
library=open(os.path.join(folder,'original-library.txt'),encoding='utf-8').read()
r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation='material_configure',directory=library))));assert r['ok'],r
with open(os.path.join(folder,'new-before.json'),'w') as f:json.dump(dict(pid=EXPECTED_PID,document=oldSerial,restoredLibrary=library),f)
doc.Modified=False # Owned fixture only; baseline already saved separately.
assert Rhino.RhinoApp.RunScript('_-New _None',False)
print('Native New on owned fixture requested; library preference restored')

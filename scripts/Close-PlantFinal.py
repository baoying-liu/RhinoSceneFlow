import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
folder=os.path.join(OUTPUT_DIR,'plants015');setup=json.load(open(os.path.join(folder,'setup.json')));jobs=json.load(open(os.path.join(folder,'jobs-status.json')))
assert jobs.get('organizePreservedIdentityImagesAndSize')
doc=__rhino_doc__
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
options=Rhino.FileIO.FileWriteOptions();options.UpdateDocumentPath=True;options.SuppressDialogBoxes=True;path=os.path.join(folder,'Plants015-Final-'+str(EXPECTED_PID)+'.3dm');assert not os.path.exists(path);assert doc.WriteFile(path,options) and not doc.Modified
api('material_configure',directory=setup['originalLibrary']);api('plant_settings',settings=setup['oldSettings'])
with open(os.path.join(folder,'before-last-restart.json'),'w') as f:json.dump(dict(pid=EXPECTED_PID,model=path,originalLibraryRestored=True),f,indent=2)
print('Owned model saved; original library and settings restored')

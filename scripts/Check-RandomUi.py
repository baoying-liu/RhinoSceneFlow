import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'random014');setup=json.load(open(os.path.join(folder,'setup.json')));ui=json.load(open(os.path.join(folder,'ui-start.json')))
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
assert api('material_random_status',jobId=ui['cancelJob'])['status']=='cancelled'
assert not api('material_quick_status')['busy']
asset=next(a for a in api('material_library')['assets'] if a['id']==setup['asset']['id'])
assert asset['randomization']['mode']=='macro' and asset['randomization']['tiles']==2 and asset['randomization']['seed']==88
native=[]
for oid in setup['objects']:
 obj=doc.Objects.FindId(System.Guid(oid));m=obj.GetRenderMaterial(True).ToMaterial(Rhino.Render.RenderTexture.TextureGeneration.Disallow);t=m.GetBitmapTexture();b=System.Drawing.Bitmap(t.FileName)
 assert b.Width==256 and b.Height==256
 native.append(t.FileName);b.Dispose();t.Dispose();m.Dispose()
path=os.path.join(folder,'Random014-Demo-'+str(EXPECTED_PID)+'.3dm');assert not os.path.exists(path)
options=Rhino.FileIO.FileWriteOptions();options.UpdateDocumentPath=True;options.SuppressDialogBoxes=True
assert doc.WriteFile(path,options) and not doc.Modified
api('material_configure',directory=setup['originalLibrary'])
report=dict(pid=EXPECTED_PID,cancelledWithoutCommit=True,manualUiDraftApplied=True,native=native,originalLibraryRestored=True,model=path)
with open(os.path.join(folder,'ui-verified.json'),'w') as f:json.dump(report,f,indent=2)
print(json.dumps(report))

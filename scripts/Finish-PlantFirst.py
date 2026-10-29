import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'plants015');setup=json.load(open(os.path.join(folder,'setup.json')))
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
job=api('material_chat_status',jobId=setup['aiJob']);assert job['status']=='completed' and job['plant'] and not job['material'],job
asset=next(a for a in api('plant_library')['assets'] if a['id']==job['plant']);assert asset['plant']['scientificName']=='Acer rubrum' and asset['plant']['family']=='Sapindaceae' and asset['plant']['sources']
bitmap=System.Drawing.Bitmap(job['imagePath']);size=[bitmap.Width,bitmap.Height];assert size[0]>128 and size[1]>256;bitmap.Dispose()
api('plant_place',assetId=asset['id'],points=[[-4,2,0]],seed=42,minScale=1,maxScale=1,mirror=False)
path=os.path.join(folder,'Plants015-Demo-'+str(EXPECTED_PID)+'.3dm');assert not os.path.exists(path)
options=Rhino.FileIO.FileWriteOptions();options.UpdateDocumentPath=True;options.SuppressDialogBoxes=True;assert doc.WriteFile(path,options) and not doc.Modified
with open(os.path.join(folder,'ai-verified.json'),'w') as f:json.dump(dict(pid=EXPECTED_PID,job=job,asset=asset,size=size,model=path,freshRealAiPng=True),f,indent=2)
api('material_configure',directory=setup['originalLibrary']);api('plant_settings',settings=setup['oldSettings'])
print(json.dumps(dict(realAiPlant=True,scientificName=asset['plant']['scientificName'],size=size,model=path)))

import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi,SceneFlowPlugin
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'uv-v012');s=json.load(open(os.path.join(folder,'guards-rebuild.json')))
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))));assert r['ok'],r;return r['result']
job=api('material_unwrap_status',jobId=s['rebuildJob']['id']);assert job['status']=='completed',job;target=s['ids'][1];api('material_apply',assetId=s['asset'],objects=[target]);before=api('material_uv_status',objects=[target])
asset=next(a for a in api('material_library')['assets'] if a['id']==s['asset'])
for i in range(6):
 asset['widthMeters']=.6 if i%2==0 else 1;asset['heightMeters']=.3 if i%2==0 else 1;asset=api('material_update',asset=asset);api('material_apply',assetId=s['asset'],objects=[target]);row=api('material_uv_renderer',objectId=target);assert row['primitives'][0]['uvError']==0 and row['primitives'][0]['normalError']==0
 assert api('material_uv_status',objects=[target])==before
 # Verify the provider's actual material copy preserves physical texture repeats.
 obj=doc.Objects.FindId(System.Guid(target));vp=Rhino.DocObjects.ViewportInfo(doc.Views.ActiveView.ActiveViewport)
 from Rhino.Render.CustomRenderMeshes import RenderMeshProvider
 primitives,flags=obj.RenderMeshes(Rhino.Geometry.MeshType.Render,vp,System.Collections.Generic.List[Rhino.DocObjects.InstanceObject](),RenderMeshProvider.Flags.IsDocumentObject,SceneFlowPlugin.Instance,None)
 instance=next(iter(primitives));native=instance.Material.ToMaterial(Rhino.Render.RenderTexture.TextureGeneration.Disallow);texture=native.GetBitmapTexture();assert abs(texture.UvwTransform.M00-1/asset['widthMeters'])<1e-6 and abs(texture.UvwTransform.M11-1/asset['heightMeters'])<1e-6
 texture.Dispose();native.Dispose();primitives.Dispose();vp.Dispose()
s.update(materialSwitchPassed=True,physicalRepeatPassed=True,uvReused=True)
model=os.path.join(folder,'UV-Continuity-Brick.3dm');assert doc.WriteFile(model,Rhino.FileIO.FileWriteOptions());s['model']=model
with open(os.path.join(folder,'guards-verified.json'),'w') as f:json.dump(s,f,indent=2)
print('PASS: six actual native material switches, physical repeats and stable UV; model saved')

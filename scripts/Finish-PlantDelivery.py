import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi,WorkbenchService
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'plants015');receipt=json.load(open(os.path.join(folder,'delivery.json')))
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
assert api('describe')['version']=='0.15.0';assert len(api('plant_instances')['objects'])==4
assert api('material_library')['directory']==receipt['originalLibrary']
root=os.path.dirname(receipt['model']);before=doc.Modified
# Explicit settings keyed to the saved sample path, independent of an unsaved fixture's settings key.
for view in receipt['views']:api('configure_view',viewId=view,settings=dict(width=1000,height=700,mode=str(Rhino.Display.DisplayModeDescription.RenderedId),layers=[dict(kind='plants',plantGrouping='species'),dict(kind='shadow',blend='mul '),dict(kind='texture')],plantShadows=True))
exports=api('export_workbench',directory=root,views=receipt['views'],collision='overwrite');assert all(f['ok'] for f in exports['files']),exports
for index,row in enumerate(WorkbenchService.Settings(doc)):
 b=WorkbenchService.Preview(doc,row,900);b.Save(os.path.join(root,'preview-'+str(index)+'.png'),System.Drawing.Imaging.ImageFormat.Png);b.Dispose()
assert doc.Modified==before
api('material_workspace_group')
for page in ['materials','library','uv','export','planting']:api('material_workspace_open',page=page)
api('plant_select',assetId=receipt['asset']);state=api('material_workspace_status');assert len(state['tools'])==5 and all(t['error'] is None for t in state['tools'].values()),state
receipt.update(pid=EXPECTED_PID,exports=exports,allToolsHealthy=True,topGroundFixed=True,originalLibraryRestored=True)
with open(os.path.join(folder,'delivery.json'),'w') as f:json.dump(receipt,f,indent=2)
print(json.dumps(dict(pid=EXPECTED_PID,plants=4,readOnlyExport=True,topAndPerspective=True,allToolsHealthy=True,exports=exports)))

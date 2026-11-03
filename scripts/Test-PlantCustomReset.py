import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi,PlantService
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'properties017');record=json.load(open(os.path.join(folder,'setup.json')));path=os.path.join(folder,'reset.json');stage=json.load(open(path))['stage'] if os.path.exists(path) else 0
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
if stage==0:
 api('plant_edit_enter',groupId=record['group'],individualId=record['individual'])
 api('plant_individual_update',groupId=record['group'],individualId=record['individual'],custom=False)
 loose=api('plant_place',assetId=record['palette'][0]['asset'],points=[[23,8,0]],minScale=1,maxScale=1)['objects'][0]
 api('plant_loose_update',objectId=loose,assetId=record['palette'][1]['asset'],scale=.6,mirror=True)
 item=PlantService.Read(doc.Objects.FindId(System.Guid(loose)));assert item.Asset==System.Guid(record['palette'][1]['asset']) and item.Scale==.6 and item.Mirror
 doc.Objects.UnselectAll();doc.Objects.Select(System.Guid(loose));api('material_workspace_open',page='properties')
else:
 state=api('plant_group_state',groupId=record['group']);assert not state['busy'] and not state['error'] and not state['spec']['individuals'],state
 rows=json.loads(doc.Objects.FindId(System.Guid(record['group'])).Geometry.UserDictionary.GetString('SceneFlow.PlantRows.v1'));assert not any(r['id']==record['individual'] for r in rows)
 state=api('material_workspace_status');assert state['tools']['properties']['error'] is None
with open(path,'w') as f:json.dump(dict(stage=stage+1,passed=stage>=1,pid=EXPECTED_PID,looseCompatible=True),f)
print('Custom reset / loose compatibility phase '+str(stage)+' passed')

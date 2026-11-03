"""Run after UI layout ticks; changes one automatic plant and verifies RDK layer isolation."""
import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'properties017');record=json.load(open(os.path.join(folder,'setup.json')))
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
group=record['group'];state=api('plant_group_state',groupId=group);assert not state['busy'] and state['error'] is None and state['count']>5,state
obj=doc.Objects.FindId(System.Guid(group));rows=json.loads(obj.Geometry.UserDictionary.GetString('SceneFlow.PlantRows.v1'));row=next(r for r in rows if not r['manual'])
api('plant_edit_enter',groupId=group,individualId=row['id'])
asset=next(p['asset'] for p in record['palette'] if p['asset']!=row['asset'])
updated=api('plant_individual_update',groupId=group,individualId=row['id'],assetId=asset,scale=2.1,mirror=True,point=[8,8,.8])['individualId']
record.update(individual=updated,originalIndividual=row['id'],individualAsset=asset,initialCount=len(rows))
# Layer scope must not change the other layer's effective material.
ids=[System.Guid(i) for i in record['objects']]
outside=doc.Objects.FindId(ids[2]).GetRenderMaterial(True).Id
rep=api('selection_material_update',objects=[str(ids[1])],scope='layer',metallic=.2)
assert len(rep['objects'])>=2,rep
assert doc.Objects.FindId(ids[2]).GetRenderMaterial(True).Id==outside
record['layerScopePassed']=True
with open(os.path.join(folder,'setup.json'),'w') as f:json.dump(record,f,indent=2)
print(json.dumps(dict(custom=updated,layerScope=rep)))

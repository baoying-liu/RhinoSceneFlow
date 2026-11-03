import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'properties017');record=json.load(open(os.path.join(folder,'setup.json')))
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
group=record['group'];state=api('plant_group_state',groupId=group);assert not state['busy'] and state['error'] is None,state
obj=doc.Objects.FindId(System.Guid(group));rows=json.loads(obj.Geometry.UserDictionary.GetString('SceneFlow.PlantRows.v1'));row=next(r for r in rows if r['id']==record['individual'])
assert row['asset']==record['individualAsset'] and row['scale']==2.1 and row['mirror'] and abs(row['position']['z']-1.8)<1e-5,row
assert len(rows)==32 and state['spec']['individuals'][0]['attachment']['asset']==record['individualAsset']
# Save real document with custom instance and material variants for native Open regression.
path=os.path.join(folder,'SceneFlow-Properties-017.3dm');options=Rhino.FileIO.FileWriteOptions();options.UpdateDocumentPath=True;options.SuppressDialogBoxes=True
assert doc.WriteFile(path,options) and not doc.Modified
record.update(model=path,customSurvivesSeeds=True,customFollowsCarrier=True,count=len(rows),pid=EXPECTED_PID)
with open(os.path.join(folder,'setup.json'),'w') as f:json.dump(record,f,indent=2)
print(json.dumps(dict(model=path,count=len(rows),custom=row)))

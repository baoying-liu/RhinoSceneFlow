import System,json,os,clr
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import MaterialQuickController,McpApi
D=__rhino_doc__
state=json.load(open(os.path.join(OUTPUT_DIR,'worlduv','quick-generation.json')))
p=MaterialQuickController.Find(D.RuntimeSerialNumber)
r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation='material_quick_status',document=int(D.RuntimeSerialNumber)))))['result']
assert r['jobId'] is None and r['selected']==state['newAsset'],r
state['completedAssetSelected']=True
with open(os.path.join(OUTPUT_DIR,'worlduv','quick-generation.json'),'w') as f:json.dump(state,f,indent=2)
print(json.dumps(state))

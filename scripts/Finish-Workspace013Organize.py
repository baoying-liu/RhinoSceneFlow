"""Check real whole-library AI changes, filter intersection and immutable rendering identities."""
import Rhino,System,clr,json,os
from System.Reflection import BindingFlags
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'workspace013');before=json.load(open(os.path.join(folder,'organize-start.json')))
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
job=api('material_catalog_status',jobId=before['job']);assert job['status']=='completed',job
assets=api('material_library')['assets'];assert len(assets)==len(before['assets'])
for old in before['assets']:
 a=next(a for a in assets if a['id']==old['id'])
 for key in ['revision','widthMeters','heightMeters','roughness','metallic','maps','sha256']:assert a[key]==old[key],(key,a,old)
 assert a['catalogRevision']==old['catalogRevision']+1
assert api('material_inspect',objects=[str(o.Id) for o in doc.Objects])==before['bindings']
assert [(str(o.Id),int(o.Geometry.DataCRC(0))) for o in doc.Objects]==[tuple(v) for v in before['geometry']]
assert len(set(a['category'] for a in assets))<len(set(a['category'] for a in before['assets']))
a=assets[0];found=api('material_library',category=a['category'],tag=a['tags'][0]);assert any(x['id']==a['id'] for x in found['assets'])
assert len(api('material_library',category='不存在的分类')['assets'])==0
api('material_tool_settings',reuseSimilar=True)
# Empty live selection must not reuse old targets.
doc.Objects.UnselectAll();api('material_tool_apply');assert not api('material_quick_status')['busy']
assert api('material_inspect',objects=[str(o.Id) for o in doc.Objects])==before['bindings']
generated=json.load(open(os.path.join(folder,'generation-verified.json')))['asset']['id'];api('material_tool_select',assetId=generated)
fixture=json.load(open(os.path.join(folder,'setup.json')));doc.Objects.FindId(System.Guid(fixture['objects'][1])).Select(True)
report=dict(pid=EXPECTED_PID,job=job,categoriesBefore=sorted(set(a['category'] for a in before['assets'])),categoriesAfter=sorted(set(a['category'] for a in assets)),assets=assets,bindingsUnchanged=True,geometryUnchanged=True,emptySelectionRejected=True)
with open(os.path.join(folder,'organize-verified.json'),'w') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(passed=True,categoriesBefore=report['categoriesBefore'],categoriesAfter=report['categoriesAfter'],count=len(assets))))

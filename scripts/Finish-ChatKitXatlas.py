"""Apply an actually generated chat material to the retained complex fixtures and export both grouping modes."""
import Rhino,System,clr,json,os,shutil
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'xatlas');s=json.load(open(os.path.join(folder,'verified.json')));chat=json.load(open(os.path.join(folder,'chatkit-generation.json')))
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))));assert r['ok'],r;return r['result']
ids=[o['id'] for o in s['objects']];before=api('material_uv_status',objects=ids)
api('material_apply',assetId=chat['material'],objects=ids)
assert api('material_uv_status',objects=ids)==before,'Changing material must reuse calibrated xatlas UV'
for source in s['objects']:assert int(doc.Objects.FindId(System.Guid(source['id'])).Geometry.DataCRC(0))==source['crc']
example=os.path.join(os.path.dirname(OUTPUT_DIR),'examples','ChatKit-Xatlas');os.makedirs(example,exist_ok=True)
mode=next(d for d in Rhino.Display.DisplayModeDescription.GetDisplayModes() if d.EnglishName=='Arctic')
files={}
for grouping in ['material','object']:
 api('configure_view',viewId=s['view'],settings=dict(width=1024,height=768,sun=dict(useDocument=False,azimuth=135,altitude=40),layers=[dict(kind='shadow',blend='mul ',opacity=75),dict(kind='texture',textureGrouping=grouping),dict(kind='display',mode=str(mode.Id),name='Arctic')]))
 result=api('export_workbench',directory=os.path.join(example,grouping),views=[s['view']]);assert all(f['ok'] for f in result['files']),result
 target=os.path.join(example,'AI_Complex_'+('Merged' if grouping=='material' else 'ByObject')+'.psd');shutil.copy2(result['files'][0]['path'],target);files[grouping]=dict(path=target,report=result)
assert doc.WriteFile(s['model'],Rhino.FileIO.FileWriteOptions())
report=dict(pid=EXPECTED_PID,chat=chat,uv=s['result'],model=s['model'],exports=files,sourceGeometryUnchanged=True,uvReused=True)
with open(os.path.join(folder,'workflow-verified.json'),'w') as f:json.dump(report,f,indent=2)
print(json.dumps(report))

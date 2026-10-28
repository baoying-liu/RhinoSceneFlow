import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'uv-v012');s=json.load(open(os.path.join(folder,'ready.json')))
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))));assert r['ok'],r;return r['result']
rows=[]
for id,crc in zip(s['ids'],s['crc']):
 o=doc.Objects.FindId(System.Guid(id));assert o is not None and int(o.Geometry.DataCRC(0))==crc
 assert api('material_uv_status',objects=[id])[0]['status']['valid']
 row=api('material_uv_renderer',objectId=id);assert all(p['uvError']==0 and p['normalError']==0 and p['volume']>0 for p in row['primitives']);rows.append(row)
report=dict(pid=EXPECTED_PID,document=int(doc.RuntimeSerialNumber),path=doc.Path,modified=doc.Modified,restoredRenderer=rows)
with open(os.path.join(folder,'reopen-verified.json'),'w') as f:json.dump(report,f,indent=2)
# Leave only the continuous tube visible for the user's inspection; originals remain in the document.
for id in [s['ids'][0],s['ids'][2]]:doc.Objects.Hide(System.Guid(id),True)
doc.Objects.Show(System.Guid(s['guide']),True);doc.Views.Redraw()
print(json.dumps(dict(reopenedDocument=int(doc.RuntimeSerialNumber),uvErrors=[r['primitives'][0]['uvError'] for r in rows],normalErrors=[r['primitives'][0]['normalError'] for r in rows],modifiedBeforeInspection=report['modified'])))

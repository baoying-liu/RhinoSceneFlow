"""Verify real semantic reuse + live selection, then request ONE fresh AI material via the ChatKit UI."""
import Rhino,System,clr,json,os
from System.Reflection import BindingFlags
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'workspace013');fixture=json.load(open(os.path.join(folder,'setup.json')))
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
state=api('material_quick_status');assert not state['busy'],state
search=api('material_chat_status',jobId=state['lastJob']);assert search['status']=='completed' and len(search['matches'])>0 and search['material'] is None,search
first=api('material_inspect',objects=fixture['objects'][:1]);uv=api('material_uv_status',objects=fixture['objects'][:1])
assert fixture['assets'][0] in json.dumps(first),first
doc.Objects.UnselectAll();doc.Objects.FindId(System.Guid(fixture['objects'][1])).Select(True)
api('material_tool_apply');api('material_tool_settings',reuseSimilar=False) if not api('material_quick_status')['busy'] else None
# Settings are changed in the following nonblocking turn, after the UV/apply queue finishes.
report=dict(pid=EXPECTED_PID,search=search,first=first,uv=uv,secondApply=api('material_quick_status'),assetCount=len(api('material_library')['assets']))
with open(os.path.join(folder,'reuse-verified.json'),'w') as f:json.dump(report,f,indent=2)
print(json.dumps(report))

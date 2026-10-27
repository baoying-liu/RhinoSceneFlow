"""Use a non-Codex executable for one process-scoped request to verify visible failure/retry."""
import System,clr,json,os
from System.Reflection import BindingFlags
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import MaterialQuickController,McpApi
D=__rhino_doc__;p=MaterialQuickController.Find(D.RuntimeSerialNumber);assert p is not None
old=System.Environment.GetEnvironmentVariable('RHINOSCENEFLOW_CODEX')
try:
 System.Environment.SetEnvironmentVariable('RHINOSCENEFLOW_CODEX',r'C:\Program Files\dotnet\dotnet.exe')
 p.GetType().GetMethod('Generate',BindingFlags.Instance|BindingFlags.NonPublic).Invoke(p,None)
finally:System.Environment.SetEnvironmentVariable('RHINOSCENEFLOW_CODEX',old)
r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation='material_quick_status',document=int(D.RuntimeSerialNumber)))));assert r['ok'] and r['result']['jobId'],r
with open(os.path.join(OUTPUT_DIR,'materials-v09','failure-state.json'),'w') as f:json.dump(dict(pid=EXPECTED_PID,jobId=r['result']['jobId']),f)
print(json.dumps(dict(negativeRequestStarted=True)))

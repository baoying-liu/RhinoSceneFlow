import clr,json,os,System
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
folder=os.path.join(OUTPUT_DIR,'postproduction018');record=json.load(open(os.path.join(folder,'launch.json')))
result=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation='postproduction_status',jobId=record['job']))))
assert result['ok'],result
job=result['result'];assert job['status']=='completed',dict(status=job['status'],error=job['error'])
# Private loopback bearer is retained only in the ignored test receipt, never stdout.
json.dump(job,open(os.path.join(folder,'launch-private.json'),'w'),indent=2)
doc=__rhino_doc__;assert int(doc.RuntimeSerialNumber)==record['before']['serial'] and doc.Objects.Count==record['before']['objects'] and doc.Modified==record['before']['modified']
print(json.dumps(dict(status=job['status'],project=job['project'],importJob=job['importJob'],rhinoUnchanged=True)))

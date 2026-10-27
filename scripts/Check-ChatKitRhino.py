import System,json,os
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
task=System.AppDomain.CurrentDomain.GetData('SceneFlow.ChatKitProbe');assert task is not None and task.IsCompleted
result=json.loads(json.loads(task.Result))
def clean(value):
 if isinstance(value,dict):return {k:clean(v) for k,v in value.items()}
 if isinstance(value,list):return [clean(v) for v in value]
 if isinstance(value,str) and '?token=' in value:return value.split('?token=')[0]+'?token=[local-ui-token]'
 return value
result=clean(result);folder=os.path.join(OUTPUT_DIR,'xatlas');os.makedirs(folder,exist_ok=True)
with open(os.path.join(folder,'chatkit-ui.json'),'w') as f:json.dump(result,f,indent=2)
print(json.dumps(result))

"""Check object and empty-selection behavior, then begin current-layer regression."""
import Rhino,System,json,os,clr
from System.Reflection import BindingFlags
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import MaterialQuickController,McpApi
D=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'materials-v09');s=json.load(open(os.path.join(folder,'selection-state.json')));assert s['pid']==EXPECTED_PID
p=MaterialQuickController.Find(D.RuntimeSerialNumber);flags=BindingFlags.Instance|BindingFlags.NonPublic
def o(i):return D.Objects.FindId(System.Guid(s['ids'][i]))
def bound(i):return o(i).Attributes.GetUserString('RhinoSceneFlow.Material')
assert not p.Busy
assert bound(2) is not None and all(bound(i) is None for i in [0,1,3]),'Applied to stale object or redirected running operation'
s['currentObjectAndClickSnapshot']=True
D.Objects.UnselectAll();before=[bound(i) for i in range(4)]
p.GetType().GetMethod('Start',flags).Invoke(p,System.Array[System.Object]([False]));assert not p.Busy and before==[bound(i) for i in range(4)]
s['emptySelectionRejected']=True
# Current layer A must be used, even though original open target / last operation differ.
D.Objects.FindId(System.Guid(s['ids'][0])).Select(True)
p.GetType().GetField('scope',flags).GetValue(p).SelectedKey='layer'
p.GetType().GetMethod('Start',flags).Invoke(p,System.Array[System.Object]([False]));assert p.Busy
D.Objects.UnselectAll();D.Objects.FindId(System.Guid(s['ids'][2])).Select(True)
with open(os.path.join(folder,'selection-state.json'),'w') as f:json.dump(s,f,indent=2)
print(json.dumps(dict(objectSelectionPassed=True,emptySelectionPassed=True,layerApplyStarted=True)))

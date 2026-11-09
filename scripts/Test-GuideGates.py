"""Pure shared-context gate regression, synthetic pixels, zero model calls."""
import sys,uuid,copy,json
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/RhinoSceneFlow.Plugin/PostProduction'))
from board_store import Store
import canvas_context as c
out=ROOT/'artifacts/guide-gates'/uuid.uuid4().hex;out.mkdir(parents=True);s=Store(out);b=s.create('Synthetic gates');p=out/'pixel.png';Image.new('RGBA',(40,30),'#a8b9a0').save(p);a=s.put_asset(b['id'],p);root=s.append(b['id'],a,a,40,30,'source.png');child=s.branch(b['id'],root['id']);b=s.read(b['id']);r=next(x for x in b['nodes'] if x['id']==root['id']);n=next(x for x in b['nodes'] if x['id']==child['id']);r['editReference']=dict(asset=a,preview=a,width=40,height=30,sourceAsset=r['asset'],enabled=True)
assert any(x.get('editingReference') for x in c.collected(b,n)[1])
n['editReference']=dict(r['editReference'],sourceAsset=n['asset'],enabled=False)
assert not any(x.get('editingReference') for x in c.collected(b,n)[1]),'Disabling a local slot must not silently enable the parent'
n['editReference']['enabled']=True;n['annotations']=[dict(id=uuid.uuid4().hex,kind='text',text='Guide',x=10,y=10,size=16,color='#123456',enabled=True)]
sig=c.signature(b,n);n['guideControls']=dict(visible=False,specialVisible=False);n['annotations'][0]['visible']=False
assert sig==c.signature(b,n),'Eyes must be presentation only'
n['guideControls']['specialEnabled']=False;marks,refs=c.collected(b,n);assert not marks and any(x.get('editingReference') for x in refs)
n['guideControls']['enabled']=False;assert c.collected(b,n)==([],[])
n['guideControls'].update(enabled=True,specialEnabled=True);assert len(c.collected(b,n)[0])==1
report=dict(parentInheritanceWhenNoSlot=True,disabledSlotNeverReactivatesParent=True,eyesOutsideSignature=True,specialGateKeepsAppearance=True,totalGateCoversAll=True,childSettingsRetained=True,modelCalls=0,folder=str(out));(out/'verified.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))

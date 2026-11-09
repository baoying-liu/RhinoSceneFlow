"""Frame/lock independence and reference promotion/deletion; synthetic assets, no model."""
import json,sys,uuid,copy
from pathlib import Path
from PIL import Image
from fastapi import HTTPException
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/RhinoSceneFlow.Plugin/PostProduction'))
from board_store import Store
out=ROOT/'artifacts/reference-gallery'/uuid.uuid4().hex;out.mkdir(parents=True);s=Store(out);b=s.create('Gallery');bid=b['id'];p=out/'a.png';Image.new('RGB',(80,60),'#86a47b').save(p);a=s.put_asset(bid,p);root=s.append(bid,a,a,80,60,'input.png');n=s.branch(bid,root['id']);nid=n['id'];s.publish(bid,nid,a,a,80,60,'whole',{},dict(inputVersion=s.pixel_snapshot(root)))
def board():return s.read(bid)
def node(id):return next(n for n in board()['nodes'] if n['id']==id)
def ctl(id,action):return s.control(bid,id,dict(revision=board()['revision'],action=action))
def reject(fn):
 try:fn()
 except (ValueError,HTTPException):return
 raise AssertionError('Expected refusal')
old=node(nid);f={**old['frame'],'width':old['frame']['width']+50};s.patch(bid,dict(revision=board()['revision'],nodes=[dict(id=nid,frame=f)]));assert node(nid)['locked'] and node(nid)['frame']==f
reject(lambda:s.patch(bid,dict(revision=board()['revision'],nodes=[dict(id=nid,params={**node(nid)['params'],'prompt':'must stay locked'})])))
ctl(nid,'unlock');assert not node(nid)['locked'];s.patch(bid,dict(revision=board()['revision'],nodes=[dict(id=nid,params={**node(nid)['params'],'prompt':'Keep this draft when locking'})]));ctl(nid,'lock');assert node(nid)['locked'] and node(nid)['params']['prompt']=='Keep this draft when locking';reject(lambda:ctl(root['id'],'lock'));assert not node(root['id'])['locked']
r=s.append(bid,a,a,80,60,'reference.png',kind='reference');rid=r['id'];pose=node(nid)['pose'];s.patch(bid,dict(revision=board()['revision'],selectedId=nid,nodes=[dict(id=rid,pose=dict(x=pose['x']+100,y=pose['y']+100,width=100,height=75))]));before={n['id']:n['pose'] for n in board()['nodes'] if n['kind']=='image'}
ctl(rid,'delete');assert node(rid)['deleted'];assert before=={n['id']:n['pose'] for n in board()['nodes'] if n['kind']=='image'};assert board()['selectedId']==nid
s.history(bid,dict(revision=board()['revision'],direction='undo'));assert not node(rid)['deleted'];ctl(rid,'convertToInput');converted=node(rid);assert converted['kind']=='image' and converted['original'] and not converted['locked'] and converted['asset']==a
s.history(bid,dict(revision=board()['revision'],direction='undo'));assert node(rid)['kind']=='reference';assert s.preference()['referenceAutoLocate'] is False;s.preference(referenceAutoLocate=True);assert s.preference()['referenceAutoLocate'] is True;reject(lambda:s.preference(referenceAutoLocate='true'))
report=dict(frameEditableWhileLocked=True,contentStillProtected=True,manualRelock=True,originalNeverContentLocked=True,referenceDeleteKeepsLayoutAndAnchor=True,conversionKeepsIdentityAndPixels=True,conversionUndo=True,referenceLocatePreference=True,modelCalls=0,folder=str(out));(out/'verified.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))

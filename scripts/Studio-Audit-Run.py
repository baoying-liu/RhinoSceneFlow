"""Incremental owned Hillside integration audit; original Platform MCP only."""
import importlib.machinery,json,os,sys,time,uuid,shutil
from pathlib import Path
m=importlib.machinery.SourceFileLoader('audit',str(Path(__file__).with_name('Studio-Audit-Mcp.py'))).load_module()
ROOT=m.ROOT; latest=ROOT/'artifacts/feature-audit-20261109/latest.json';r=m.load(latest);out=Path(r['folder']);c=m.StudioMcp(out)
def save():m.write(latest,r);m.write(out/'session.json',r)
def node(b,id):return next(n for n in b['nodes'] if n['id']==id)
def check(name,ok,**details):
 v=dict(name=name,passed=bool(ok),**details);r['checks'].append(v);save();print(json.dumps(v,ensure_ascii=False),flush=True)
def main():
 cmd=sys.argv[1];bid=r['board']
 if cmd=='branch':
  b=c.board(bid);a=node(b,r['wholeA']);assert not a['pending'] and a['locked']
  ui=c.api('/boards/'+bid+'/duplicate',dict(name='Hillside · UI interaction audit'));r['uiBoard']=ui['id'];save()
  bnode=c.branch(bid,a['id']);r['wholeB']=bnode['id'];save();check('child_empty_description',bnode['params']['prompt']=='' and bnode['parentId']==a['id'])
  c.control(bid,bnode['id'],'applyParent');b=c.board(bid);n=node(b,bnode['id']);p=n['pose']
  marks=[dict(id=uuid.uuid4().hex,kind='arrow',points=[[p['x']+180,p['y']+370,1],[p['x']+245,p['y']+255,1]],size=3,color='#e6a74b'),dict(id=uuid.uuid4().hex,kind='label',x=p['x']+10,y=p['y']+375,text='Facade only: warmer fine vertical cedar. Keep window divisions.',points=[],size=12,color='#e6a74b')]
  c.patch(bid,marks=marks,nodes=[dict(id=n['id'],params={**n['params'],'prompt':'Refine only the facade indicated by the arrow into warm natural fine-grain vertical cedar. Preserve every window division, opening, building silhouette, terrain, tree and camera. Annotations are guidance only and must never appear in output. Keep all other surfaces unchanged.','detail':50,'freedom':5})])
  plan=c.preflight(bid,n['id']);m.write(out/'annotated-preflight.json',plan);check('spatial_marks_in_real_preflight',len(plan['annotations'])==2 and plan['input']['id']==a['id'])
  task=c.generate(bid,n['id']);r['annotatedTask']=task['id'];save()
  # Queue behind the actual B image job, then cancel before entering the image runner.
  q=c.api('/boards/'+r['uiBoard']+'/duplicate',dict(name='Hillside · queued cancellation audit'));r['cancelBoard']=q['id'];save();qn=c.branch(q['id'],a['id']);c.patch(q['id'],nodes=[dict(id=qn['id'],params={**qn['params'],'prompt':'Cancellation audit: this queued request must never reach the image runner.'})]);qt=c.generate(q['id'],qn['id']);r['cancelTask']=qt['id'];save()
  before=c.api('/boards/'+q['id']+'/tasks');cancel=c.api('/jobs/'+qt['job']+'/cancel',{});time.sleep(.5);after=c.api('/boards/'+q['id']+'/tasks');m.write(out/'queued-cancel.json',dict(before=before,after=after,result=cancel));check('queued_cancellation',after[0]['status']=='cancelled',phaseBefore=before[0]['phase'])
 elif cmd=='status':
  ts=c.api('/boards/'+bid+'/tasks');m.write(out/'tasks.json',ts);print(json.dumps([dict(id=t['id'],node=t['node'],status=t['status'],phase=t['phase'],error=t.get('error')) for t in ts],ensure_ascii=False))
 elif cmd=='hd':
  b=c.board(bid);base=node(b,r.get('wholeB',r['wholeA']));assert not base['pending'];n=c.branch(bid,base['id'],stage='detail');r['hd']=n['id'];save();c.patch(bid,nodes=[dict(id=n['id'],params={**n['params'],'outputSize':1024,'tileSize':1024,'overlap':64})]);plan=c.preflight(bid,n['id'],'detail');m.write(out/'hd-preflight.json',plan);check('hd_pinned_approved_input',plan['input']['id']==base['id'] and plan['ready']);t=c.generate(bid,n['id'],'detail');r['hdTask']=t['id'];save();print(t)
 elif cmd=='update':
  b=c.board(bid);a=node(b,r['wholeA']);r['beforeUpdate']=dict(asset=a['asset'],versionId=a['versionId'],params=a['params']);save();c.control(bid,a['id'],'unlock');p=a['pose']
  def poly(kind,coords):return dict(id=uuid.uuid4().hex,kind=kind,points=[[p['x']+x,p['y']+y,1] for x,y in coords],size=3,color='#e6a74b',closed=True)
  marks=b.get('marks',[])+[poly('edit',[(205,207),(333,270),(333,304),(205,254)]),poly('protect',[(208,180),(269,196),(269,233),(208,212)])]
  c.patch(bid,marks=marks,nodes=[dict(id=a['id'],params={**a['params'],'prompt':'Within the editable mask only, render warm fine vertical natural cedar cladding. Preserve facade geometry and every opening. No text, no redesign. Outside the editable mask must stay identical.','freedom':5})]);plan=c.preflight(bid,a['id']);m.write(out/'update-preflight.json',plan);check('localized_preflight_mask',0<plan['editablePixels']<plan['totalPixels']/10,inputIsOriginal=plan['input']['id']==r['sourceNode']);t=c.generate(bid,a['id']);r['updateTask']=t['id'];save();print('Real masked update started')
 elif cmd=='states':
  b=c.api('/boards/'+r['previousUiBoard']+'/duplicate',dict(name='Hillside · provenance and recovery audit'));s=b['id'];r['stateBoard']=s;save();c.api('/boards/'+s+'/tasks');c.patch(s,marks=[]);c.control(s,r['wholeA'],'cancel');b=c.board(s);a=node(b,r['wholeA']);root=node(b,r['sourceNode'])
  sn=c.branch(s,a['id'],sibling=True);r['sibling']=sn['id'];save();check('sibling_parent_and_settings',sn['parentId']==a['parentId'] and sn['params']['prompt']=='' and sn['params']['detail']==a['params']['detail'])
  ch=c.branch(s,a['id']);r['stateChild']=ch['id'];save();check('child_pending_white_contract',ch['pending'] and not ch['locked'] and ch['params']['prompt']=='')
  c.control(s,ch['id'],'applyParent');ch=node(c.board(s),ch['id']);check('apply_parent_is_guidance_not_generation',ch['pending'] and ch.get('draftBaseApplied') and not (ch.get('source') or {}).get('receipt'))
  before=c.board(s);c.control(s,a['id'],'delete');b=c.board(s);check('delete_subtree',node(b,a['id'])['deleted'] and node(b,ch['id'])['deleted'] and not node(b,sn['id'])['deleted']);c.api('/boards/'+s+'/history',dict(revision=b['revision'],direction='undo'));b=c.board(s);check('undo_subtree',not node(b,a['id'])['deleted'] and not node(b,ch['id'])['deleted']);c.api('/boards/'+s+'/history',dict(revision=b['revision'],direction='redo'));check('redo_subtree',node(c.board(s),ch['id'])['deleted']);c.control(s,a['id'],'restoreDeleted')
  c.control(s,a['id'],'unlock');c.patch(s,nodes=[dict(id=a['id'],params={**a['params'],'detail':87})]);check('parameter_dirty_and_cancel',node(c.board(s),a['id'])['dirty']);c.control(s,a['id'],'cancel');aa=node(c.board(s),a['id']);check('cancel_restores_baseline',aa['params']['detail']==a['params']['detail'] and aa['locked'] and aa['asset']==a['asset'])
  c.control(s,a['id'],'expand');check('backup_capacity_plus_three',node(c.board(s),a['id'])['backupLimit']==5);c.control(s,a['id'],'autoPrune',enabled=True);check('backup_autoprune_control',node(c.board(s),a['id'])['autoPrune']);c.control(s,a['id'],'followBackupDefault')
  # Actual text assistant writes an archive intent note; no synthetic AI summary.
  d=c.api('/boards/'+s+'/describe',dict(node=a['id'],archive=True,message='Summarize only the visual changes from the parent for reversible archive bypass. Keep it short.'))
  r['archiveJob']=d['job'];save();print('Archive text job started',flush=True)
 elif cmd=='archive-poll':
  s=r['stateBoard'];j=c.api('/jobs/'+r['archiveJob']);m.write(out/'archive-job.json',j);print(dict(status=j['status'],stage=j['stage']))
  if j['status']=='completed':
   b=c.board(s);a=node(b,r['wholeA']);check('real_ai_archive_summary',a['archived'] and bool(a.get('archiveSummary')))
   plan=c.preflight(s,r['stateChild']);m.write(out/'archive-preflight.json',plan);check('archived_effective_parent_and_notes',plan['input']['id']==r['sourceNode'] and bool(plan['notes']));c.control(s,a['id'],'restore');check('unarchive_restores_ancestry',node(c.board(s),r['stateChild'])['parentId']==a['id'])
   package=c.api('/boards/'+s+'/save',{});shutil.copyfile(package['path'],out/'hillside-audit.sflowboard');restored=c.api('/boards/'+s+'/import-path',dict(path=package['path']));m.write(out/'package-roundtrip.json',restored);print('roundtrip keys',list(restored));
 elif cmd=='verify-update':
  from PIL import Image
  import numpy as np,hashlib
  b=c.board(bid);a=node(b,r['wholeA']);child=node(b,r['wholeB']);folder=Path(os.environ['LOCALAPPDATA'])/'RhinoSceneFlow/postproduction/boards'/bid/'tasks'/r['updateTask'];x=np.array(Image.open(folder/'base.png').convert('RGBA'));y=np.array(Image.open(folder/'result.png').convert('RGBA'));mask=np.array(Image.open(folder/'mask.png').convert('L'));check('actual_masked_update_pixel_identity',np.array_equal(x[mask==0],y[mask==0]) and np.array_equal(x[:,:,3],y[:,:,3]),editablePixels=int((mask>0).sum()),changedPixels=int(np.any(x!=y,axis=2).sum()))
  check('immutable_backup_and_downstream_stale',len(a['versions'])==1 and a['versions'][0]['asset']==r['beforeUpdate']['asset'] and child['inputChanged'] and child['input']['versionId']==r['beforeUpdate']['versionId']);plan=c.preflight(bid,child['id']);check('next_input_latest_but_comparison_pinned',plan['input']['versionId']==a['versionId'] and child['input']['versionId']!=a['versionId']);m.write(out/'downstream-preflight.json',plan)
  v=a['versions'][0];assets=Path(os.environ['LOCALAPPDATA'])/'RhinoSceneFlow/postproduction/boards'/bid/'assets';digest=hashlib.sha256((assets/v['asset']).read_bytes()).hexdigest();currentAsset=a['asset'];c.control(bid,a['id'],'checkout',version=v['versionId']);checked=node(c.board(bid),a['id']);check('backup_checkout_non_destructive',checked['asset']==currentAsset and checked['checkout']==v['versionId'] and not checked['locked'] and hashlib.sha256((assets/v['asset']).read_bytes()).hexdigest()==digest);c.control(bid,a['id'],'cancel');check('backup_cancel_preserves_current',node(c.board(bid),a['id'])['asset']==currentAsset)
  # Test admission guard without another image call; restore shared preference immediately.
  prefs=c.api('/board-preferences');c.control(bid,a['id'],'unlock')
  try:
   c.api('/board-preferences',dict(backupLimit=1),'PUT')
   try:c.generate(bid,a['id']);raise AssertionError('Capacity unexpectedly allowed generation')
   except RuntimeError as e:check('backup_capacity_blocks_before_model','Backup capacity reached' in str(e))
  finally:c.api('/board-preferences',dict(backupLimit=prefs['backupLimit']),'PUT');c.control(bid,a['id'],'cancel')
  shutil.copyfile(folder/'result.png',out/'masked-update.png');m.write(out/'post-update-board.json',c.board(bid))
 elif cmd=='exports':
  from PIL import Image
  b=c.board(bid);n=node(b,r.get('wholeB',r['wholeA']));assert not n['pending']
  for fmt in ['png','jpg','webp']:
   v=c.api('/boards/'+bid+'/export',dict(node=n['id'],format=fmt,blend=100));dest=out/('export.'+fmt);shutil.copyfile(v['path'],dest)
   im=Image.open(dest);im.load();check('export_'+fmt,im.size==(n['width'],n['height']),mode=im.mode,format=im.format)
  v=c.api('/boards/'+bid+'/save',{});m.write(out/'package.json',v);print(v)
 else:raise ValueError(cmd)
main()

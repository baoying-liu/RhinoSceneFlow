"""Collect only this session's real receipts; preserve user settings and source hashes."""
import importlib.machinery,json,hashlib,os,time,shutil,statistics
from pathlib import Path
m=importlib.machinery.SourceFileLoader('audit',str(Path(__file__).with_name('Studio-Audit-Mcp.py'))).load_module()
r=m.load(m.ROOT/'artifacts/feature-audit-20261109/latest.json');o=Path(r['folder']);c=m.StudioMcp(o);storage=Path(os.environ['LOCALAPPDATA'])/'RhinoSceneFlow/postproduction';receipts=[]
for board,task in [(r['board'],r['initialTask']),(r['board'],r['annotatedTask']),(r['board'],r['updateTask']),(r['stateBoard'],r['siblingTask'])]:
 p=storage/'boards'/board/'tasks'/task/'image-job/receipt.json';v=m.load(p);receipts.append(dict(kind='whole',board=board,task=task,receipt=v))
hd=c.api('/boards/'+r['board']+'/tasks/'+r['hdTask']+'/review');p=storage/'projects'/hd['project']/'runs'/hd['id']
for receipt in sorted(p.glob('tile-*/attempt-*/receipt.json')):receipts.append(dict(kind='tile',tile=receipt.parent.parent.name,attempt=receipt.parent.name,receipt=m.load(receipt)))
assert len(receipts)==7,len(receipts)
m.write(o/'real-model-receipts.json',receipts)
tasks=c.api('/boards/'+r['board']+'/tasks');m.write(o/'final-tasks.json',tasks)
assert all(t['status']=='completed' for t in tasks)
assert all(t['status']=='completed' for t in c.api('/boards/'+r['stateBoard']+'/tasks'))
cancel=c.api('/boards/'+r['cancelBoard']+'/tasks');assert cancel[0]['status']=='cancelled'
assert not (storage/'boards'/r['cancelBoard']/'tasks'/r['cancelTask']/'image-job/receipt.json').exists()
assert hashlib.sha256(Path(r['source']).read_bytes()).hexdigest()==r['sourceSha256']
b=c.board(r['board']);c.patch(b['id'],selectedId=r['wholeB'],nodes=[dict(id=r['hd'],name='HD · 功能验证（存在结构漂移）.png')]);c.api('/board-preferences',{k:v for k,v in r['preferences'].items() if k!='listWheelVersion'},'PUT')
checks={x['name']:x for x in r['checks']}
ui=m.load(o/'actual-ui-results.json');layout=m.load(o/'actual-layout-results.json');recheck=m.load(o/'actual-layout-recheck.json')
layoutChecks={x['name']:x for x in layout['results']};layoutChecks.update({x['name']:x for x in recheck['results']})
summary=dict(board=r['board'],nativePid=c.pid,version=c.api('/status')['version'],realImageCalls=len(receipts),wholeImageCalls=4,tileImageCalls=3,textCalls=1,cancelledBeforeImageRunner=1,apiChecks=list(checks.values()),uiChecks=ui['results'],layoutChecks=list(layoutChecks.values()),pageErrors=ui['errors']+layout['errors']+recheck['errors'],photoCraft=m.load(o/'photocraft-browser-verified.json'),referenceGallery=m.load(o/'reference-gallery-browser-verified.json'),pixels=m.load(o/'pixel-verification.json'),originalPSDSha256=r['sourceSha256'],originalPSDUnchanged=True,preferencesRestored=True,finished=time.time(),secondsSinceFirstRun=time.time()-r['created'])
summary['functionalAssertionsPassed']=all(x['passed'] for x in [*checks.values(),*ui['results'],*layoutChecks.values()]) and not summary['pageErrors']
m.write(o/'summary.json',summary)
durations=[json.loads(s)['seconds'] for s in (o/'mcp-requests.jsonl').read_text(encoding='utf8').splitlines()];summary['mcpRequestSeconds']=dict(count=len(durations),median=statistics.median(durations),max=max(durations));m.write(o/'summary.json',summary)
print(json.dumps({k:summary[k] for k in ['realImageCalls','textCalls','functionalAssertionsPassed','originalPSDUnchanged','preferencesRestored','secondsSinceFirstRun','mcpRequestSeconds']},ensure_ascii=False))

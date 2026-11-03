"""Read-only verification of B's actual HTTP file handoff. Never prints its bearer URL."""
import argparse,hashlib,json,time,urllib.request
from pathlib import Path
from urllib.parse import urlparse,parse_qs
root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--shutdown',action='store_true');args=parser.parse_args()
folder=root/'artifacts/rhino-B/postproduction018'
launch=json.loads((folder/'launch-private.json').read_text())
parsed=urlparse(launch['url']);token=parse_qs(parsed.fragment)['token'][0];base=parsed.scheme+'://'+parsed.netloc
def call(route,body=None):
    with urllib.request.urlopen(urllib.request.Request(base+'/api'+route,data=b'{}' if body else None,headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'}),timeout=30) as response:return json.loads(response.read())
for _ in range(120):
    job=call('/jobs/'+launch['importJob'])
    if job['status'] not in ('queued','running'):break
    time.sleep(.5)
assert job['status']=='completed',job
project=call('/projects/'+launch['project']);record=json.loads((folder/'launch.json').read_text())
assert project['context']['document']==record['before']['serial']
assert project['document']['sha256']==hashlib.sha256(Path(record['psd']).read_bytes()).hexdigest()
plan=call('/projects/'+launch['project']+'/plan')
verified=dict(project=project['id'],layers=len(project['document']['layers']),tiles=len(plan['tiles']),sourceSha256=project['document']['sha256'],contextMatches=True,status=call('/status'))
(folder/'handoff.json').write_text(json.dumps(verified,indent=2))
print(json.dumps(verified))
if args.shutdown:call('/shutdown',True)

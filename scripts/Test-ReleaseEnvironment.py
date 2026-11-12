"""Actual B Settings/account/runtime/update guards; no installation, login or image calls."""
import json
import subprocess
import sys
import time
from pathlib import Path

root = Path(__file__).resolve().parents[1]
out = root / 'artifacts/release-environment'
out.mkdir(parents=True, exist_ok=True)

def run(name, source):
    path = out / (name + '.py')
    path.write_text(source, encoding='utf8')
    value = subprocess.check_output([sys.executable, str(root/'scripts/Rhino-Mcp.py'), 'run_python', str(path)], encoding='utf8')
    result = json.loads(value)
    content = result.get('result', {}).get('content', [])
    for item in content:
        if item.get('type') == 'text':
            for line in item['text'].splitlines():
                if line.startswith('RELEASE_TEST:'):
                    return json.loads(line[len('RELEASE_TEST:'):])
    raise RuntimeError('Native test did not return a receipt: ' + str(content)[:1200])

header = r'''
import System,Rhino,clr,json
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi,SceneFlowWorkspace
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
def api(op,**kw):
    r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,**kw))))
    assert r['ok'],r
    return r['result']
'''
started = run('start', header + r'''
r=api('release_status');assert r['sandbox'] and not r['managed']
SceneFlowWorkspace.Open('settings')
f=System.Reflection.BindingFlags.Public|System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Static
assembly=clr.GetClrType(SceneFlowWorkspace).Assembly
release=assembly.GetType('RhinoSceneFlow.Plugin.ReleaseService')
try:
    task=release.GetMethod('DownloadAsync',f).Invoke(None,None)
    task.GetAwaiter().GetResult()
    raise Exception('Sandbox allowed a production update')
except System.Exception as e:assert 'production_only' in str(e)
initial=api('plugin_settings')
from Eto.Forms import Button
hosts=clr.GetClrType(SceneFlowWorkspace).GetField('Hosts',f).GetValue(None)
try:
    api('plugin_settings',settings=dict(initial,language='zh',textMode='short',showIcons=False))
    assert u'检测' in [c.Text for c in hosts['settings'].Children if isinstance(c,Button)]
    api('plugin_settings',settings=dict(initial,language='en',textMode='full',showIcons=False))
    labels=[c.Text for c in hosts['settings'].Children if isinstance(c,Button)]
    assert 'Check environment and sign-in' in labels
    assert all(not any(u'一'<=v<=u'鿿' for v in (text or '')) for text in labels)
finally:api('plugin_settings',settings=initial)
api('connection_check');api('release_check')
print('RELEASE_TEST:'+json.dumps(dict(pid=EXPECTED_PID,version=r['version'],sandboxGuard=True,languageModes=True)))
''')
deadline = time.monotonic() + 40
while True:
    state = run('status', header + r'''
c=api('connection_status');r=api('release_status')
print('RELEASE_TEST:'+json.dumps(dict(pid=EXPECTED_PID,connection=c,release=r)))
''')
    if not state['connection']['busy'] and not state['release']['busy']:
        break
    if time.monotonic() > deadline:
        raise TimeoutError('Account/release checks did not finish')
    time.sleep(1)
assert state['pid'] == started['pid']
assert state['connection']['platformLoaded']
assert state['connection']['runtime'] == 'ready', state['connection']
assert state['release']['status'] in ('current', 'available', 'not_public', 'offline', 'rate_limit')
receipt = dict(started=started, result=state, realModelCalls=0, productionInstalled=False)
(out/'verified.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf8')
print(json.dumps(receipt, ensure_ascii=True))

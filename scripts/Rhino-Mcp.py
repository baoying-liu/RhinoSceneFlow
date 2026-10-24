"""Execute a discovered Rhino MCP tool only against the sandbox manager's live B instance."""
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

root = Path(__file__).resolve().parents[1]
status = json.loads(subprocess.check_output([sys.executable, str(root / 'scripts/Sandbox-Mcp.py'), 'workspace_status']))
if status['ChannelId'] not in ('1cee488700ad42f59492743cc4a2a3fe', '0d327c4c84f644f089b73834ffd93cfe') or not status.get('Pid'):
    raise RuntimeError('B channel is not running')
monitor = json.loads((Path(status['LastStartupDirectory']) / 'monitor-status.json').read_text(encoding='utf-8-sig'))
if monitor['Pid'] != status['Pid'] or not monitor.get('PlatformAllowed'):
    raise RuntimeError('B instance identity mismatch')
name = sys.argv[1]
if name == 'run_python':
    source = Path(sys.argv[2]).read_text(encoding='utf-8-sig')
    prefix = f"EXPECTED_PID = {status['Pid']}\nOUTPUT_DIR = {str(root / 'artifacts/rhino-B')!r}\n"
    # Always return normally to Platform even when the test fails; retain full traceback as evidence.
    wrapped = "try:\n" + '\n'.join('    ' + line for line in (prefix + source).splitlines())
    wrapped += "\nexcept Exception:\n    import traceback\n    print(traceback.format_exc())\n"
    arguments = {'script': wrapped}
else:
    arguments = json.loads(Path(sys.argv[2]).read_text(encoding='utf-8-sig')) if len(sys.argv) > 2 else {}
body = {'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call', 'params': {'name': name, 'arguments': arguments}}
request = urllib.request.Request(f"http://127.0.0.1:{monitor['Port']}/", data=json.dumps(body).encode(),
    headers={'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream'})
with urllib.request.urlopen(request, timeout=300) as response:
    payload = json.loads(response.read())
if 'error' in payload or payload.get('result', {}).get('isError'):
    raise RuntimeError(json.dumps(payload))
print(json.dumps(payload, ensure_ascii=True, indent=2))

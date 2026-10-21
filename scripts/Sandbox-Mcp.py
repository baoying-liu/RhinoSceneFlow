"""Local sandbox manager client, pinned to channel B. Never prints or persists credentials."""
import json
import os
import sys
import urllib.request
from pathlib import Path

config_root = Path(os.environ['LOCALAPPDATA']) / 'RhinoDevSandbox'
catalog = json.loads((config_root / 'config/channels.json').read_text(encoding='utf-8-sig'))
channel = next(c for c in catalog['Channels'] if c['Name'] == 'B' and not c.get('Archived'))
channel_id = channel['Id']
if channel_id != '1cee488700ad42f59492743cc4a2a3fe':
    raise RuntimeError('B channel identity changed; review target before proceeding')
workspace = json.loads((config_root / 'config/workspace.json').read_text(encoding='utf-8-sig'))
port = workspace['Mcp']['Port']
if port != 19540:
    raise RuntimeError('Expected management MCP port 19540')
token = catalog['Tokens'][channel_id]
url = f'http://127.0.0.1:{port}/mcp/channels/{channel_id}'

def rpc(method, params, request_id=1):
    body = {'jsonrpc': '2.0', 'method': method, 'params': params}
    if request_id is not None:
        body['id'] = request_id
    request = urllib.request.Request(url, data=json.dumps(body).encode(), headers={
        'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream',
        'Authorization': 'Bearer ' + token,
    })
    with urllib.request.urlopen(request, timeout=300) as response:
        raw = response.read().decode()
    if not raw:
        return None
    if raw.lstrip().startswith('{'):
        return json.loads(raw)
    messages = [json.loads(line[5:].strip()) for line in raw.splitlines() if line.startswith('data:')]
    return next((m for m in messages if m.get('id') == request_id), messages[-1] if messages else None)

rpc('initialize', {'protocolVersion': '2025-03-26', 'capabilities': {},
    'clientInfo': {'name': 'RhinoSceneFlow-sandbox-validation', 'version': '0.1.1'}})
rpc('notifications/initialized', {}, None)
if len(sys.argv) < 2 or sys.argv[1] == '--tools':
    result = rpc('tools/list', {})
else:
    name = sys.argv[1]
    arguments = json.loads(Path(sys.argv[2]).read_text(encoding='utf-8-sig')) if len(sys.argv) > 2 else {}
    result = rpc('tools/call', {'name': name, 'arguments': arguments})
if result and 'error' in result:
    raise RuntimeError(json.dumps(result['error']))
payload = result.get('result', {}) if result else {}
if payload.get('isError'):
    raise RuntimeError(json.dumps(payload))
content = payload.get('content', [])
if len(content) == 1 and content[0].get('type') == 'text':
    try:
        payload = json.loads(content[0]['text'])
    except ValueError:
        payload = content[0]['text']
if isinstance(payload, dict) and 'ChannelId' in payload and 'Projects' in payload:
    payload = {k: v for k, v in payload.items() if k not in ('RecentJobs', 'ProductionPromotion')}
print(json.dumps(payload, ensure_ascii=True, indent=2))

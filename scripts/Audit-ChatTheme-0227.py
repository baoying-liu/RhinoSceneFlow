import importlib.machinery,json,subprocess,sys
from pathlib import Path
m=importlib.machinery.SourceFileLoader('audit','scripts/Audit-UX20261110.py').load_module()
r=m.run("""import Rhino,System,json,clr
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
flags=System.Reflection.BindingFlags.Public|System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Instance
r=json.loads(McpApi.Execute('{"apiVersion":1,"operation":"material_workspace_open","page":"materials"}'))['result'];p=Rhino.UI.Panels.GetPanel(System.Guid(r['pages'][0]['panelId']));tool=p.GetType().GetProperty('Tool',flags).GetValue(p);chat=tool.GetType().GetField('chat',flags).GetValue(tool);browser=chat.GetType().GetField('Browser',flags).GetValue(chat)
host=chat.GetType().GetField('host',flags).GetValue(chat)
print('UX_AUDIT:'+json.dumps(dict(url=str(host.GetType().GetProperty('Url',flags).GetValue(host)))))
""")
v=subprocess.run(['C:/Program Files/nodejs/node.exe','scripts/Test-ChatThemeBrowser.cjs'],input=json.dumps(r),capture_output=True,text=True,encoding='utf8',errors='replace');token=r['url'].split('token=')[1].split('&')[0];print((v.stdout+v.stderr).replace(token,'[REDACTED]'));sys.exit(v.returncode)

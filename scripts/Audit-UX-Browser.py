import json,os,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'artifacts/ux-audit-20261110';s=json.loads((Path(os.environ['LOCALAPPDATA'])/'RhinoSceneFlow/postproduction/service.json').read_text(encoding='utf-8-sig'))
args=sys.argv[1:]
if args==['open']:args=['open',f"http://127.0.0.1:{s['port']}/#token={s['token']}",'--browser','msedge']
r=subprocess.run(['npx.cmd','--yes','--package','@playwright/cli','playwright-cli','-s=sf-ux-20261110',*args],cwd=out,capture_output=True,text=True,encoding='utf8',errors='replace')
print((r.stdout+r.stderr).replace(s['token'],'[REDACTED]'));sys.exit(r.returncode)

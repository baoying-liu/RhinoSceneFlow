"""No account mutation or executable invocation: late install and path discovery."""
import os,sys,tempfile
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src/RhinoSceneFlow.Plugin/PostProduction'))
from codex_discovery import find_codex
with tempfile.TemporaryDirectory(dir=ROOT/'artifacts') as temp:
    home=Path(temp)
    with patch.object(Path,'home',return_value=home),patch.dict(os.environ,{'PATH':'','RHINOSCENEFLOW_CODEX':''}):
        assert find_codex()==''
        late=home/'.codex/bin/codex.exe';late.parent.mkdir(parents=True);late.write_bytes(b'fixture; never executed')
        assert find_codex()==str(late.resolve())
        assert find_codex(str(home/'missing.exe'))==str(late.resolve())
        configured=home/'pinned.exe';configured.write_bytes(b'pinned; never executed')
        assert find_codex(str(configured))==str(configured.resolve())
        assert find_codex('relative.exe')==str(late.resolve())
print('PASS: absent -> late-installed Codex, stale path fallback, explicit pin and no executable invocation.')

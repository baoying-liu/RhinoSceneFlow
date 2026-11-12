"""Re-discover a local Codex after installation, without accepting executables from HTTP."""
import os
from pathlib import Path


def find_codex(configured=''):
    candidates = [configured, os.environ.get('RHINOSCENEFLOW_CODEX', '')]
    candidates += [str(Path(p.strip('"'))/'codex.exe') for p in os.environ.get('PATH', '').split(os.pathsep) if p]
    candidates.append(str(Path.home()/'.codex/bin/codex.exe'))
    extensions = Path.home()/'.vscode/extensions'
    try:
        candidates += [str(p/'bin/windows-x86_64/codex.exe') for p in sorted(extensions.glob('openai.chatgpt-*'), key=lambda p:p.stat().st_mtime, reverse=True)]
    except OSError:
        pass
    for candidate in candidates:
        if candidate and Path(candidate).is_absolute() and Path(candidate).is_file():
            return str(Path(candidate).resolve())
    return ''

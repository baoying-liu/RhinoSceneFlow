"""Independently decode the material demo PSD with psd-tools (outside Rhino)."""
import json
from pathlib import Path
import numpy as np
from psd_tools import PSDImage

root = Path(__file__).resolve().parents[1] / 'artifacts/rhino-B/materials/demo'
report = json.loads((root / 'export-report.json').read_text())
assert report['ok'] and report['stateUnchanged'], report
files = report['result']['files']
assert len(files) == 1 and files[0]['ok'], files
psd = PSDImage.open(files[0]['path'])
assert psd.size == (320, 200), psd.size
layers = list(reversed(list(psd)))
names = [layer.name for layer in layers]
assert len(names) == 3 and names[:2] == ['Rendered', 'Shadow'], names
assert layers[2].is_group(), names
preview = np.asarray(psd.topil().convert('RGBA')).astype(int)
recomposed = np.asarray(psd.composite(force=True).convert('RGBA')).astype(int)
error = int(np.abs(preview - recomposed).max())
assert error <= 2, error
result = dict(ok=True, size=psd.size, topToBottom=names, maxRecomposeError=error)
(root / 'export-verified.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, ensure_ascii=True))

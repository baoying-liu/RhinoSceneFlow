"""Decode real Rhino exports using psd-tools, independently of the plugin implementation."""
import json
from pathlib import Path
import sys
import numpy as np
from psd_tools import PSDImage

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'artifacts/rhino-B')
report = json.loads((root / 'smoke.json').read_text(encoding='utf-8-sig'))
assert report['complete']
checks = []
for case in report['cases']:
    psd = PSDImage.open(case['path'])
    assert psd.size == (case['width'], case['height'])
    assert len(psd) == 3, [(l.name, l.bbox) for l in psd]
    names = [l.name for l in psd]
    assert any('SameRed' in n and 'Building' in n for n in names), names
    assert not any('Hidden' in n for n in names), names
    merged = psd.topil().convert('RGBA')
    recomposed = psd.composite(force=True).convert('RGBA')
    def premul(data):
        values = np.array(data).astype(float)
        values[:, :, :3] *= values[:, :, 3:4] / 255
        return values
    error = float(np.abs(premul(merged) - premul(recomposed)).max())
    assert error <= 2.5, error
    assert merged.getpixel((0, 0))[3] == 0
    for probe in case['probes']:
        x, y = int(probe['x']), int(probe['y'])
        pixel = merged.getpixel((x, y))
        assert pixel == tuple(probe['rgb'] + [255]), (case['name'], probe, pixel)
        if probe['label'] == 'front':
            blue = next(l for l in psd if 'Paving' in l.name)
            alpha = blue.topil().convert('RGBA')
            if blue.left <= x < blue.right and blue.top <= y < blue.bottom:
                assert alpha.getpixel((x-blue.left, y-blue.top))[3] == 0, 'Hidden blue pixels leaked into foreground'
    assert case['state_unchanged']
    merged.save(root / (case['name'] + '-psd-preview.png'))
    checks.append({'view':case['name'], 'layers':names, 'size':list(psd.size), 'maxCompositeError':error,
        'elapsedMilliseconds':case['export']['elapsedMilliseconds'], 'probesPassed':len(case['probes'])})
(root / 'verified.json').write_text(json.dumps({'ok':True,'pid':report['pid'],'checks':checks}, indent=2), encoding='utf-8')
print(json.dumps({'ok':True,'pid':report['pid'],'checks':checks}, indent=2))

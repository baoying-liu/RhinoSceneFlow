"""Independent PSD decoding and analytic/source-surface direct-light oracle."""
from pathlib import Path
from psd_tools import PSDImage
import json,numpy as np
root=Path(__file__).resolve().parents[1]/'artifacts/rhino-B/accuracy'
report=json.loads((root/'direct-report.json').read_text())
assert report['restored'] and len(report['cases'])==2
results=[]
for case in report['cases']:
    psd=PSDImage.open(case['result']['export']['path']);layer=psd[0]
    rgba=np.array(layer.topil());alpha=np.zeros((psd.height,psd.width),dtype=np.uint8)
    alpha[layer.top:layer.bottom,layer.left:layer.right]=rgba[:,:,3]
    failures=[];dark=lit=partial=0
    for s in case['samples']:
        expected=round(sum(s['shadow'])*255/4)
        actual=int(alpha[s['y'],s['x']])
        if abs(actual-expected)>1:failures.append(dict(sample=s,alpha=actual,expected=expected))
        dark+=expected==255;lit+=expected==0;partial+=0<expected<255
    result=dict(name=case['name'],samples=len(case['samples']),failures=len(failures),dark=dark,lit=lit,partial=partial)
    results.append(result)
    psd.composite().save(root/('direct-'+case['name']+'.png'))
    assert not failures,(result,failures[:12])
    assert dark>20 and lit>20
(root/'direct-verified.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results))

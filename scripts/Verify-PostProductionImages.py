"""Independent PNG decoder and saved provenance/readonly-pixel oracle for actual app results."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--data',required=True);args=parser.parse_args()
root=Path(args.data).resolve();request=json.loads((root/'batch-request.json').read_text())
folder=root/'projects'/request['project']/'runs'/request['batch']
state=json.loads((folder/'run.json').read_text(encoding='utf-8'))
assert state['status']=='completed' and state['output']['accepted']==2 and not state['output']['partial']
base=np.asarray(Image.open(folder/'base.png').convert('RGBA'))
output_path=folder/state['output']['image'];output=np.asarray(Image.open(output_path).convert('RGBA'))
mask=np.asarray(Image.open(folder/'edit-mask.png').convert('L'))
protected=np.asarray(Image.open(folder/'protected-mask.png').convert('L'))
assert output.shape==base.shape==(900,1200,4)
assert np.array_equal(output[mask==0],base[mask==0])
assert np.array_equal(output[protected>0],base[protected>0])
assert np.array_equal(output[:,:,3],base[:,:,3])
changed=int(np.count_nonzero(np.any(output!=base,axis=2)));assert changed>1000
receipts=[]
for path in (root/'projects'/request['project']/'runs').rglob('receipt.json'):
 receipt=json.loads(path.read_text());assert receipt['newImage']
 assert hashlib.sha256((path.parent/'generated.png').read_bytes()).hexdigest()==receipt['sha256']
 receipts.append(receipt['thread'])
assert len(receipts)==3 and len(set(receipts))==3,'Expected one real style + two real tile calls'
report=dict(width=1200,height=900,actualImageCalls=3,acceptedTiles=2,reusedTile=True,protectedPixels=int(np.count_nonzero(protected)),readonlyPixels=int(np.count_nonzero(mask==0)),readonlyExact=True,alphaExact=True,changedPixels=changed,sha256=hashlib.sha256(output_path.read_bytes()).hexdigest(),output=str(output_path),quality=[t['quality'] for t in state['tiles']])
(root/'verified-final.json').write_text(json.dumps(report,indent=2))
examples=ROOT/'artifacts/examples/PostProduction-v019';examples.mkdir(parents=True,exist_ok=True)
import shutil
shutil.copyfile(output_path,examples/'Hillside-AI-Result.png');shutil.copyfile(folder/'base.png',examples/'Hillside-Original.png')
comparison=Image.new('RGB',(1200,450),'white')
for index,image in enumerate((Image.fromarray(base),Image.fromarray(output))):
 image.thumbnail((600,450));comparison.paste(image,(index*600,0),image.getchannel('A'))
comparison.save(examples/'Before-After.png')
print(json.dumps({k:v for k,v in report.items() if k!='quality'}))

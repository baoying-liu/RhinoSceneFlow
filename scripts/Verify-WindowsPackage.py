"""Verify the distributable archive without registering a plugin in formal Rhino."""
from pathlib import Path
import hashlib,json,subprocess,zipfile,os
from PIL import Image

root=Path(__file__).resolve().parents[1]
latest=json.loads((root/'artifacts/distribution-input/latest.json').read_text(encoding='utf-8-sig'))
zip_path=Path(latest['zip']);work=root/'artifacts/distribution-validation'
bundle=work/'extracted-final'/Path(latest['directory']).name
manifest=json.loads((bundle/'SHA256SUMS.json').read_text(encoding='utf-8-sig'))
for item in manifest:
    assert hashlib.sha256((bundle/item['path']).read_bytes()).hexdigest().upper()==item['sha256']
assert not any(p.name.lower() in {'auth.json','chat.sqlite','deployment.json','workspace.json','channels.json'} for p in bundle.rglob('*'))
yak=bundle/latest['yak'];payload=work/'payload-final'
with zipfile.ZipFile(yak) as archive:
    assert not any(n.lower().endswith('.pdb') for n in archive.namelist())
    archive.extractall(payload)
assert hashlib.sha256((payload/'RhinoSceneFlow.Plugin.rhp').read_bytes()).hexdigest().upper()==latest['pluginSha256']
required=['RhinoSceneFlow.Core.dll','geometry3Sharp.dll','SceneFlow.UvWorker.exe','ChatKit/server.py','ChatKit/index.html','runtimes/win-x64/native/WebView2Loader.dll','TextureWorker/SceneFlow.TextureWorker.exe','TextureWorker/coreclr.dll','TextureWorker/System.Windows.Forms.dll','xatlas-LICENSE.txt','geometry3Sharp-LICENSE.txt','FastNoiseLite-LICENSE.txt']
for name in required:assert (payload/name).is_file(),name
source=work/'worker-input.png';im=Image.new('RGB',(32,32),(130,155,100));im.save(source)
key='D'*64;output=work/('worker-result-'+os.urandom(4).hex())
request=dict(version=1,key=key,maps={'baseColor':str(source)},sha256={'baseColor':hashlib.sha256(source.read_bytes()).hexdigest().upper()},settings=dict(mode='stochastic',seed=19,strength=.12,tiles=2,rotate=True),seed=19,widthMeters=2,heightMeters=1,outputDirectory=str(output))
request_path=work/'worker-request.json';request_path.write_text(json.dumps(request))
env=os.environ.copy();env['DOTNET_ROOT']=str(work/'missing-dotnet');env['DOTNET_ROOT_X64']=env['DOTNET_ROOT'];env['DOTNET_MULTILEVEL_LOOKUP']='0'
run=subprocess.run([str(payload/'TextureWorker/SceneFlow.TextureWorker.exe'),str(request_path)],env=env,capture_output=True,text=True,timeout=45)
assert run.returncode==0,run.stderr
result=json.loads((output/'manifest.json').read_text());assert (result['widthMeters'],result['heightMeters'])==(4,2)
assert Image.open(output/result['maps']['baseColor']).size==(64,64)
report=dict(zip=str(zip_path),size=zip_path.stat().st_size,sha256=hashlib.sha256(zip_path.read_bytes()).hexdigest(),yak=yak.name,pluginSha256=latest['pluginSha256'],manifestFiles=len(manifest),noCredentialsOrUserData=True,selfContainedWorker=True,formalRhinoRegistrationChanged=False)
(work/'verified.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))

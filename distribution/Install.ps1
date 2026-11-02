param([switch]$StageOnly,[string]$RuntimeDirectory=(Join-Path $env:LOCALAPPDATA 'RhinoSceneFlow/chatkit-runtime'))
$ErrorActionPreference='Stop'
if(-not [Environment]::Is64BitOperatingSystem){throw 'Windows x64 is required.'}
$bundleRoot=$PSScriptRoot
$manifest=Get-Content -LiteralPath (Join-Path $bundleRoot 'SHA256SUMS.json') -Raw | ConvertFrom-Json
foreach($entry in $manifest){
    $file=Join-Path $bundleRoot $entry.path
    if(-not(Test-Path -LiteralPath $file -PathType Leaf)){throw "Missing package file: $($entry.path)"}
    if((Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash -ne $entry.sha256){throw "Package integrity check failed: $($entry.path)"}
}
$metadata=Get-Content -LiteralPath (Join-Path $bundleRoot 'package.json') -Raw | ConvertFrom-Json
$rhinoSystem=Join-Path $env:ProgramFiles 'Rhino 8/System'
$yak=Join-Path $rhinoSystem 'Yak.exe'
if(-not $StageOnly){
    if(Get-Process Rhino -ErrorAction SilentlyContinue){throw 'Save your models and close Rhino before installing. No process will be closed automatically.'}
    if(-not(Test-Path -LiteralPath $yak)){throw 'Install Rhino 8 for Windows first (default installation path required by this helper).'}
    $sdk=[Reflection.AssemblyName]::GetAssemblyName((Join-Path $rhinoSystem 'RhinoCommon.dll')).Version
    if($sdk -lt [version]$metadata.minimumRhino){throw "Rhino $($metadata.minimumRhino) or newer is required. Please update Rhino 8."}
}
# Only this application's dedicated runtime is created. No system Python, PATH,
# account configuration, API key or existing material library is changed.
$python=Join-Path $RuntimeDirectory 'Scripts/python.exe'
if(-not(Test-Path -LiteralPath $python)){
    $scripts=Join-Path $RuntimeDirectory 'Scripts';New-Item -ItemType Directory -Path $scripts -Force | Out-Null
    Expand-Archive -LiteralPath (Join-Path $bundleRoot 'Runtime/python-3.14.10-embed-amd64.zip') -DestinationPath $scripts -Force
    @('python314.zip','.','Lib/site-packages','import site') | Set-Content -LiteralPath (Join-Path $scripts 'python314._pth') -Encoding Ascii
}
$probe=@'
import sys
try:
    import chatkit,fastapi,uvicorn
    from importlib.metadata import version
    assert version('openai-chatkit')=='1.6.5' and version('fastapi')=='0.162.0' and version('uvicorn')=='0.54.0' and version('python-multipart')=='0.0.32'
except Exception:
    sys.exit(1)
'@
& $python -I -X utf8 -c $probe
if($LASTEXITCODE -ne 0){
    $embedded=Test-Path -LiteralPath (Join-Path $RuntimeDirectory 'Scripts/python314._pth')
    if($embedded){
        $site=Join-Path $RuntimeDirectory 'Scripts/Lib/site-packages';New-Item -ItemType Directory -Force -Path $site | Out-Null
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        $pipWheels=@(Get-ChildItem -LiteralPath (Join-Path $bundleRoot 'Runtime/wheels') -Filter 'pip-*.whl')
        if($pipWheels.Count -ne 1){throw 'Exactly one bundled pip wheel is required.'}
        # Bootstrap pip from its bundled wheel, using the standard wheel layout.
        $archive=[IO.Compression.ZipFile]::OpenRead($pipWheels[0].FullName)
        try{foreach($entry in $archive.Entries){
            if(-not $entry.Name){continue}
            $target=[IO.Path]::GetFullPath((Join-Path $site $entry.FullName))
            if(-not $target.StartsWith([IO.Path]::GetFullPath($site)+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw 'Invalid wheel entry.'}
            New-Item -ItemType Directory -Force -Path (Split-Path -Parent $target) | Out-Null
            [IO.Compression.ZipFileExtensions]::ExtractToFile($entry,$target,$true)
        }}finally{$archive.Dispose()}
        & $python -I -X utf8 -m pip install --disable-pip-version-check --no-index --find-links (Join-Path $bundleRoot 'Runtime/wheels') --target $site --no-compile -r (Join-Path $bundleRoot 'Runtime/requirements-lock.txt')
    }else{
        & $python -I -X utf8 -m pip install --disable-pip-version-check --no-index --find-links (Join-Path $bundleRoot 'Runtime/wheels') -r (Join-Path $bundleRoot 'Runtime/requirements-lock.txt')
    }
    if($LASTEXITCODE -ne 0){throw 'Offline ChatKit dependency installation failed. See the output above.'}
}
& $python -I -X utf8 -c "import chatkit,fastapi,uvicorn; from importlib.metadata import version; assert version('openai-chatkit')=='1.6.5'; print('ChatKit runtime OK')"
if($LASTEXITCODE -ne 0){throw 'ChatKit runtime validation failed.'}
& $python -I -X utf8 -m pip check
if($LASTEXITCODE -ne 0){throw 'Python dependency consistency check failed.'}
if($StageOnly){Write-Output "Staging test complete: $RuntimeDirectory. Rhino registration was not changed.";exit 0}
$package=Join-Path $bundleRoot $metadata.yak
Unblock-File -LiteralPath $package
& $yak install $package
if($LASTEXITCODE -ne 0){throw 'Rhino Package Manager installation failed. The ChatKit runtime is installed; you can drag the .yak file into Rhino manually.'}
Write-Output ''
Write-Output 'Installed. Open Rhino 8 and run RhinoSceneFlow.'
Write-Output 'AI generation requires your own signed-in Codex installation and Internet access.'

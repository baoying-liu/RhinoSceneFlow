param([string]$RuntimeDirectory=(Join-Path $env:LOCALAPPDATA 'RhinoSceneFlow/chatkit-runtime'))
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
if(-not(Test-Path -LiteralPath (Join-Path $RuntimeDirectory 'Scripts/python.exe'))){
    # Prefer the Windows Python launcher over the inactive WindowsApps alias.
    $pythonLauncher=Get-Command py -ErrorAction SilentlyContinue
    if($pythonLauncher){& $pythonLauncher.Source -3 -m venv $RuntimeDirectory}
    else{python -m venv $RuntimeDirectory}
    if($LASTEXITCODE -ne 0){throw 'Python 3.10+ is required.'}
}
& (Join-Path $RuntimeDirectory 'Scripts/python.exe') -m pip install -r (Join-Path $root 'src/RhinoSceneFlow.Plugin/ChatKit/requirements.txt')
if($LASTEXITCODE -ne 0){throw 'ChatKit runtime setup failed.'}
& (Join-Path $RuntimeDirectory 'Scripts/python.exe') -m pip check
if($LASTEXITCODE -ne 0){throw 'ChatKit runtime dependencies are inconsistent.'}
Write-Output $RuntimeDirectory

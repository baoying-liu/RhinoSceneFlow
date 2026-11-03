param([string]$RuntimeDirectory=(Join-Path $env:LOCALAPPDATA 'RhinoSceneFlow/chatkit-runtime'))
$ErrorActionPreference='Stop'
& (Join-Path $PSScriptRoot 'Setup-ChatKit.ps1') -RuntimeDirectory $RuntimeDirectory
& (Join-Path $RuntimeDirectory 'Scripts/python.exe') -m pip install -r (Join-Path $PSScriptRoot '../src/RhinoSceneFlow.Plugin/PostProduction/requirements.txt')
if($LASTEXITCODE -ne 0){throw 'Postproduction runtime setup failed.'}
& (Join-Path $RuntimeDirectory 'Scripts/python.exe') -m pip check
if($LASTEXITCODE -ne 0){throw 'Postproduction runtime dependencies are inconsistent.'}

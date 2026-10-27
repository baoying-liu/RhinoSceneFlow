param([string]$RuntimeDirectory=(Join-Path $env:LOCALAPPDATA 'RhinoSceneFlow/chatkit-runtime'))
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
if(-not(Test-Path -LiteralPath (Join-Path $RuntimeDirectory 'Scripts/python.exe'))){python -m venv $RuntimeDirectory;if($LASTEXITCODE -ne 0){throw 'Python 3.10+ is required.'}}
& (Join-Path $RuntimeDirectory 'Scripts/python.exe') -m pip install -r (Join-Path $root 'src/RhinoSceneFlow.Plugin/ChatKit/requirements.txt')
if($LASTEXITCODE -ne 0){throw 'ChatKit runtime setup failed.'}
Write-Output $RuntimeDirectory

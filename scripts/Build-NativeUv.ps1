param([string]$Configuration='Release')
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$vswhere=Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
$vsRoot=& $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
if(-not $vsRoot){throw 'Visual Studio C++ tools are required for xatlas.'}
$cmake=Join-Path $vsRoot 'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe'
$build=Join-Path $root 'artifacts/native-uv-build'
& $cmake -S (Join-Path $root 'src/RhinoSceneFlow.UvWorker') -B $build -G 'Visual Studio 17 2022' -A x64
if($LASTEXITCODE -ne 0){throw 'Native UV configure failed.'}
& $cmake --build $build --config $Configuration
if($LASTEXITCODE -ne 0){throw 'Native UV build failed.'}

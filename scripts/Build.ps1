param([string]$Configuration = 'Release')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
try {
    dotnet build RhinoSceneFlow.sln -c $Configuration
    if ($LASTEXITCODE -ne 0) { throw 'Build failed.' }
    dotnet run --project tests/RhinoSceneFlow.Validation -c $Configuration --no-build -- artifacts/validation
    if ($LASTEXITCODE -ne 0) { throw 'Validation failed.' }
    $packagePath = Join-Path $projectRoot 'artifacts/package/RhinoSceneFlow'
    New-Item -ItemType Directory -Path $packagePath -Force | Out-Null
    $outputPath = Join-Path $projectRoot "src/RhinoSceneFlow.Plugin/bin/$Configuration/net8.0-windows"
    foreach ($name in @('RhinoSceneFlow.Plugin.rhp', 'RhinoSceneFlow.rui', 'RhinoSceneFlow.Core.dll', 'RhinoSceneFlow.Plugin.deps.json', 'geometry3Sharp.dll', 'SceneFlow.UvWorker.exe')) {
        Copy-Item -LiteralPath (Join-Path $outputPath $name) -Destination $packagePath -Force
    }
    Copy-Item -LiteralPath (Join-Path $projectRoot 'third-party/geometry3Sharp-LICENSE.txt') -Destination $packagePath -Force
    Copy-Item -LiteralPath (Join-Path $projectRoot 'third-party/xatlas/LICENSE') -Destination (Join-Path $packagePath 'xatlas-LICENSE.txt') -Force
    foreach ($name in @('Microsoft.Web.WebView2.Core.dll','Microsoft.Web.WebView2.Wpf.dll')) {
        Copy-Item -LiteralPath (Join-Path $outputPath $name) -Destination $packagePath -Force
    }
    foreach ($name in @('runtimes','ChatKit','TextureWorker','PostProduction')) {
        Copy-Item -LiteralPath (Join-Path $outputPath $name) -Destination $packagePath -Recurse -Force
    }
    Copy-Item -LiteralPath (Join-Path $projectRoot 'third-party/FastNoiseLite/LICENSE') -Destination (Join-Path $packagePath 'FastNoiseLite-LICENSE.txt') -Force
    foreach ($arch in @('win-x86','win-arm64')) {
        $staleLoader = Join-Path $packagePath "runtimes/$arch/native/WebView2Loader.dll"
        if (Test-Path -LiteralPath $staleLoader) { Remove-Item -LiteralPath $staleLoader -Force }
    }
    Write-Output "Plugin package: $packagePath"
} finally { Pop-Location }

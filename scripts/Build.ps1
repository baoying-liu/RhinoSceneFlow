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
    foreach ($name in @('RhinoSceneFlow.Plugin.rhp', 'RhinoSceneFlow.Core.dll', 'RhinoSceneFlow.Plugin.deps.json')) {
        Copy-Item -LiteralPath (Join-Path $outputPath $name) -Destination $packagePath -Force
    }
    Write-Output "Plugin package: $packagePath"
} finally { Pop-Location }

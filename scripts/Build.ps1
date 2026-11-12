param([string]$Configuration = 'Release',[string]$RhinoSystem='')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
try {
    Push-Location (Join-Path $projectRoot 'web/postproduction')
    try {
        node build.cjs
        if ($LASTEXITCODE -ne 0) { throw 'Studio web build failed.' }
    } finally { Pop-Location }
    $buildArgs=@('build','RhinoSceneFlow.sln','-c',$Configuration)
    if($RhinoSystem){$buildArgs+=('-p:RhinoSystem='+[IO.Path]::GetFullPath($RhinoSystem))}
    & dotnet @buildArgs
    if ($LASTEXITCODE -ne 0) { throw 'Build failed.' }
    dotnet run --project tests/RhinoSceneFlow.Validation -c $Configuration --no-build -- artifacts/validation
    if ($LASTEXITCODE -ne 0) { throw 'Validation failed.' }
    dotnet run --project tests/RhinoSceneFlow.UiText.Validation -c $Configuration
    if ($LASTEXITCODE -ne 0) { throw 'UI text validation failed.' }
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
    $projectVersion = ([xml](Get-Content -LiteralPath (Join-Path $projectRoot 'Directory.Build.props') -Raw)).Project.PropertyGroup.Version
    $webVersion = (Get-Content -LiteralPath (Join-Path $packagePath 'PostProduction/version.txt') -Raw).Trim()
    if ($webVersion -ne $projectVersion) { throw "Studio service version $webVersion differs from plugin $projectVersion." }
    if (-not (Get-Content -LiteralPath (Join-Path $packagePath 'PostProduction/board.js') -Raw).Contains('"' + $projectVersion + '"')) {
        throw 'Studio browser bundle does not contain the current project version.'
    }
    Copy-Item -LiteralPath (Join-Path $projectRoot 'third-party/FastNoiseLite/LICENSE') -Destination (Join-Path $packagePath 'FastNoiseLite-LICENSE.txt') -Force
    Copy-Item -LiteralPath (Join-Path $projectRoot 'src/RhinoSceneFlow.Plugin/Resources/InterfaceIcons/LICENSE.txt') -Destination (Join-Path $packagePath 'Lucide-LICENSE.txt') -Force
    foreach ($arch in @('win-x86','win-arm64')) {
        $staleLoader = Join-Path $packagePath "runtimes/$arch/native/WebView2Loader.dll"
        if (Test-Path -LiteralPath $staleLoader) { Remove-Item -LiteralPath $staleLoader -Force }
    }
    Write-Output "Plugin package: $packagePath"
} finally { Pop-Location }

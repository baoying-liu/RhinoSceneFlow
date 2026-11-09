param([Parameter(Mandatory=$true)][string]$DeploymentDirectory)
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$version=([xml](Get-Content -LiteralPath (Join-Path $root 'Directory.Build.props') -Raw)).Project.PropertyGroup.Version
$tag=Get-Date -Format 'yyyyMMdd-HHmmss'
$release=Join-Path $root "artifacts/releases/RhinoSceneFlow-$version-Windows-x64-$tag"
$yakStage=Join-Path $root "artifacts/distribution-build/$tag/yak"
$inputRoot=Join-Path $root 'artifacts/distribution-input'
# Refuse an old ChatKit-only offline runtime rather than ship a broken postproduction tool.
foreach($pattern in @('psd_tools-1.10.9-*.whl','pillow-11.3.0-*.whl','numpy-2.2.6-*.whl','opencv_python_headless-4.12.0.88-*.whl','pyvips-3.2.0-*.whl','pyvips_binary-8.18.7-*.whl')){
    if(-not(Get-ChildItem -Path (Join-Path $inputRoot "wheels/$pattern") -ErrorAction SilentlyContinue)){throw "Postproduction offline wheel missing: $pattern. Refresh and validate the embedded Python wheel set before making a ZIP."}
}
New-Item -ItemType Directory -Force -Path $release,$yakStage,(Join-Path $release 'Packages'),(Join-Path $release 'Runtime/wheels') | Out-Null
# Curated, already tested deployment only. Exclude debug data, sandbox manifests,
# local settings, credentials, user models and material/chat libraries.
foreach($name in @('RhinoSceneFlow.Plugin.rhp','RhinoSceneFlow.rui','RhinoSceneFlow.Plugin.deps.json','RhinoSceneFlow.Core.dll','geometry3Sharp.dll','SceneFlow.UvWorker.exe','Microsoft.Web.WebView2.Core.dll','Microsoft.Web.WebView2.Wpf.dll')){
    Copy-Item -LiteralPath (Join-Path $DeploymentDirectory $name) -Destination $yakStage
}
foreach($name in @('ChatKit','runtimes','PostProduction')){Copy-Item -LiteralPath (Join-Path $DeploymentDirectory $name) -Destination $yakStage -Recurse}
Copy-Item -LiteralPath (Join-Path $inputRoot 'TextureWorker') -Destination $yakStage -Recurse
Get-ChildItem -LiteralPath (Join-Path $yakStage 'TextureWorker') -Filter '*.pdb' -File | Remove-Item
Copy-Item -LiteralPath (Join-Path $root 'third-party/geometry3Sharp-LICENSE.txt') -Destination $yakStage
Copy-Item -LiteralPath (Join-Path $root 'third-party/xatlas/LICENSE') -Destination (Join-Path $yakStage 'xatlas-LICENSE.txt')
Copy-Item -LiteralPath (Join-Path $root 'third-party/FastNoiseLite/LICENSE') -Destination (Join-Path $yakStage 'FastNoiseLite-LICENSE.txt')
foreach($notice in @('LICENSE.txt','NOTICE.txt')){
    Copy-Item -LiteralPath (Join-Path $env:USERPROFILE ".nuget/packages/microsoft.web.webview2/1.0.4314.35/$notice") -Destination (Join-Path $yakStage "WebView2-$notice")
}
@("name: rhinosceneflow","version: $version",'authors:','- RhinoSceneFlow','description: AI assets, real-world UV, planting and layered PSD workflow. Windows x64 test build.','keywords:','- guid:8b902013-73dd-4227-b45b-896f6a33f134') | Set-Content -LiteralPath (Join-Path $yakStage 'manifest.yml') -Encoding Ascii
Push-Location $yakStage
try{& 'C:/Program Files/Rhino 8/System/Yak.exe' build --platform win;if($LASTEXITCODE -ne 0){throw 'Yak build failed.'}}finally{Pop-Location}
$yakFiles=@(Get-ChildItem -LiteralPath $yakStage -Filter '*.yak' -File);if($yakFiles.Count -ne 1){throw 'Expected one Yak package.'}
Copy-Item -LiteralPath $yakFiles[0].FullName -Destination (Join-Path $release 'Packages')
foreach($file in Get-ChildItem -LiteralPath (Join-Path $root 'distribution') -File){Copy-Item -LiteralPath $file.FullName -Destination $release}
Copy-Item -LiteralPath (Join-Path $inputRoot 'python-3.14.10-embed-amd64.zip') -Destination (Join-Path $release 'Runtime')
Copy-Item -Path (Join-Path $inputRoot 'wheels/*.whl') -Destination (Join-Path $release 'Runtime/wheels')
$locked=Get-ChildItem -LiteralPath (Join-Path $release 'Runtime/wheels') -Filter '*.whl' | Where-Object {$_.Name -notlike 'pip-*'} | ForEach-Object { $parts=$_.Name.Split('-');$parts[0].Replace('_','-')+'=='+$parts[1] }
$locked | Sort-Object | Set-Content -LiteralPath (Join-Path $release 'Runtime/requirements-lock.txt') -Encoding Ascii
$metadata=[ordered]@{name='RhinoSceneFlow';version=$version;platform='win-x64';minimumRhino='8.34';yak='Packages/'+$yakFiles[0].Name;python='3.14.10';deployment=(Split-Path -Leaf $DeploymentDirectory);pluginSha256=(Get-FileHash -LiteralPath (Join-Path $yakStage 'RhinoSceneFlow.Plugin.rhp')).Hash;runtime='offline embedded CPython and pinned wheels';textureWorker='self-contained win-x64';containsPersonalData=$false}
$metadata | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $release 'package.json') -Encoding UTF8
$hashes=@(Get-ChildItem -LiteralPath $release -Recurse -File | Sort-Object FullName | ForEach-Object {[ordered]@{path=$_.FullName.Substring($release.Length+1).Replace('\','/');sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash}})
$hashes | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $release 'SHA256SUMS.json') -Encoding UTF8
$zip=$release+'.zip';Compress-Archive -LiteralPath $release -DestinationPath $zip -CompressionLevel Optimal
Write-Output "Distribution ZIP: $zip"
@{directory=$release;zip=$zip;yak=$metadata.yak;pluginSha256=$metadata.pluginSha256} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $root 'artifacts/distribution-input/latest.json') -Encoding UTF8

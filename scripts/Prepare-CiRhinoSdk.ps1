# Build references only. Never bundle or install the proprietary Rhino host.
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$dir=Join-Path $root 'artifacts/ci-sdk'
$version='8.34.26223.11001'
$archive=Join-Path $dir "rhinocommon.$version.nupkg"
New-Item -ItemType Directory -Force -Path $dir | Out-Null
if(-not(Test-Path -LiteralPath $archive)){
    Invoke-WebRequest -UseBasicParsing -Uri "https://api.nuget.org/v3-flatcontainer/rhinocommon/$version/rhinocommon.$version.nupkg" -OutFile $archive
}
if((Get-FileHash -LiteralPath $archive).Hash -ne '2579A06D59E6E927D4C276421136E599E93CF3EB9A801F1A3A6AD129A3305B69'){throw 'Rhino SDK package integrity failure.'}
Add-Type -AssemblyName System.IO.Compression.FileSystem
$reference=Join-Path $dir 'references'
New-Item -ItemType Directory -Force -Path $reference | Out-Null
$zip=[IO.Compression.ZipFile]::OpenRead($archive)
try{
    foreach($name in @('RhinoCommon.dll','Rhino.UI.dll','Eto.dll')){
        $entry=$zip.GetEntry('lib/net7.0/'+$name)
        if(-not $entry){throw "Missing SDK reference: $name"}
        [IO.Compression.ZipFileExtensions]::ExtractToFile($entry,(Join-Path $reference $name),$true)
    }
}finally{$zip.Dispose()}
Write-Output $reference

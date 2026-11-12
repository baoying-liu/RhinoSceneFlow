param([Parameter(Mandatory=$true)][string]$RuntimeDirectory)
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$cache=Join-Path $root 'artifacts/installer-dependencies'
$wheels=Join-Path $cache 'release-wheels'
$archive=Join-Path $root 'artifacts/distribution-input/python-3.14.10-embed-amd64.zip'
if((Get-FileHash -LiteralPath $archive).Hash -ne '90905E64A840557D8C1BC4F5B74DB3D7EE85E3FFB217611CAC1C7813ACEA4159'){throw 'Embedded Python archive integrity failure.'}
$env:PIP_DISABLE_PIP_VERSION_CHECK='1'
New-Item -ItemType Directory -Force -Path $wheels | Out-Null
# Build only the pure-Python pyvips wrapper; the libvips DLL wheel is a pinned binary.
if(-not(Get-ChildItem -LiteralPath $wheels -Filter 'pyvips-3.2.0-*.whl')){
    $ErrorActionPreference='Continue'
    & py -3 -m pip wheel --no-deps --wheel-dir $wheels 'pyvips==3.2.0'
    $ErrorActionPreference='Stop'
    if($LASTEXITCODE -ne 0){throw 'Unable to build the pyvips Python wheel.'}
}
$ErrorActionPreference='Continue'
& py -3 -m pip download --only-binary=:all: --platform win_amd64 --python-version 3.14 --implementation cp --abi cp314 --find-links $wheels --dest $wheels -r (Join-Path $root 'installer/requirements.txt')
$ErrorActionPreference='Stop'
if($LASTEXITCODE -ne 0){throw 'Unable to resolve all binary release dependencies.'}
$scripts=Join-Path $RuntimeDirectory 'Scripts'
# Never overlay old site-packages into a release. Only delete this explicitly verified build-artifact target.
$resolved=[IO.Path]::GetFullPath($RuntimeDirectory)
$allowed=[IO.Path]::GetFullPath((Join-Path $root 'artifacts/installer'))+[IO.Path]::DirectorySeparatorChar
if(-not $resolved.StartsWith($allowed,[StringComparison]::OrdinalIgnoreCase) -or -not $resolved.EndsWith('\payload\Runtime',[StringComparison]::OrdinalIgnoreCase)){throw 'Runtime staging is restricted to installer build artifacts.'}
if(Test-Path -LiteralPath $resolved){Remove-Item -LiteralPath $resolved -Recurse -Force}
New-Item -ItemType Directory -Force -Path $scripts | Out-Null
Expand-Archive -LiteralPath $archive -DestinationPath $scripts -Force
$python=Join-Path $scripts 'python.exe'
if((Get-AuthenticodeSignature -LiteralPath $python).Status -ne 'Valid'){throw 'Embedded Python must have a valid signature.'}
@('python314.zip','.','Lib/site-packages','import site') | Set-Content -LiteralPath (Join-Path $scripts 'python314._pth') -Encoding Ascii
$site=Join-Path $scripts 'Lib/site-packages'
New-Item -ItemType Directory -Force -Path $site | Out-Null
# pip is bootstrapped from the already pinned offline distribution, not get-pip.py.
$pip=@(Get-ChildItem -LiteralPath (Join-Path $root 'artifacts/distribution-input/wheels') -Filter 'pip-*.whl')
if($pip.Count -ne 1){throw 'Expected one pinned pip wheel.'}
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip=[IO.Compression.ZipFile]::OpenRead($pip[0].FullName)
try{foreach($entry in $zip.Entries){if(-not $entry.Name){continue};$target=[IO.Path]::GetFullPath((Join-Path $site $entry.FullName));if(-not $target.StartsWith([IO.Path]::GetFullPath($site)+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw 'Invalid wheel path.'};New-Item -ItemType Directory -Force -Path (Split-Path -Parent $target)|Out-Null;[IO.Compression.ZipFileExtensions]::ExtractToFile($entry,$target,$true)}}finally{$zip.Dispose()}
$ErrorActionPreference='Continue'
& $python -I -X utf8 -m pip install --disable-pip-version-check --no-index --find-links $wheels --target $site --upgrade --no-compile -r (Join-Path $root 'installer/requirements.txt')
$ErrorActionPreference='Stop'
if($LASTEXITCODE -ne 0){throw 'Offline release dependency installation failed.'}
& $python -I -X utf8 -m pip check
if($LASTEXITCODE -ne 0){throw 'Release dependency consistency check failed.'}
& $python -I -X utf8 -m pip freeze --all | Set-Content -LiteralPath (Join-Path $RuntimeDirectory 'requirements-lock.txt') -Encoding UTF8
@(Get-ChildItem -LiteralPath $wheels -Filter '*.whl' | ForEach-Object {@{name=$_.Name;sha256=(Get-FileHash -LiteralPath $_.FullName).Hash}}) | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $RuntimeDirectory 'wheel-provenance.json') -Encoding UTF8
Write-Output 'Private release runtime staged; no production registration changed.'

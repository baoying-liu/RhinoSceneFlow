param([string]$Version='0.23.0')
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$output=Join-Path $root "artifacts/installer/$Version"
$msi=Join-Path $output "SceneFlow-$Version-win-x64.msi"
$exe=Join-Path $output "SceneFlow-Setup-$Version-win-x64.exe"
$out=Join-Path $root ('artifacts/installer-tests/'+$Version)
New-Item -ItemType Directory -Force -Path $out | Out-Null
$key='HKCU:\Software\McNeel\Rhinoceros\8.0\Plug-ins\8b902013-73dd-4227-b45b-896f6a33f134'
function Registration { if(Test-Path -LiteralPath $key){return (Get-ItemProperty -LiteralPath $key).FileName};return $null }
$before=Registration
foreach($relative in @('THIRD-PARTY-NOTICES.md','Getting-Started.md','Notices/dotnet/LICENSE.txt','Notices/dotnet/THIRD-PARTY-NOTICES.txt','Notices/libvips/LICENSE.txt','Notices/libvips/THIRD-PARTY-NOTICES.md','Notices/libvips/SOURCES.md')){
    if(-not(Test-Path -LiteralPath (Join-Path $output "payload/$relative"))){throw "Missing public distribution notice: $relative"}
}
foreach($test in @(@{Name='InstallGuard.dll';Text='请先保存并关闭正式 Rhino'},@{Name='SceneFlow.Prerequisites.exe';Text='请先安装 Rhino 8.34+'})){
    $bytes=[IO.File]::ReadAllBytes((Join-Path $output $test.Name))
    if(-not [Text.Encoding]::Unicode.GetString($bytes).Contains($test.Text)){throw ('Native installer Unicode strings are damaged: '+$test.Name)}
}

# Read MSI tables directly; do not run install/repair/uninstall on the user's production Rhino.
$installer=New-Object -ComObject WindowsInstaller.Installer
$db=$installer.OpenDatabase($msi,0)
function Rows([string]$Sql){
    $view=$db.OpenView($Sql);$null=$view.Execute()
    $columns=$view.ColumnInfo(0);$count=$columns.FieldCount()
    $rows=[Collections.Generic.List[object]]::new()
    while($record=$view.Fetch()){$row=@();for($i=1;$i -le $count;$i++){$row+= $record.StringData($i)};$rows.Add($row)}
    $null=$view.Close();return ,$rows.ToArray()
}
$registry=Rows "SELECT ``Key``,``Name``,``Value`` FROM ``Registry`` WHERE ``Name`` = 'FileName'"
if(-not($registry | Where-Object {$_[0] -eq 'Software\McNeel\Rhinoceros\8.0\Plug-ins\8b902013-73dd-4227-b45b-896f6a33f134' -and $_[1] -eq 'FileName' -and $_[2] -eq '[INSTALLFOLDER]RhinoSceneFlow.Plugin.rhp'})){throw 'Missing standard Rhino registration.'}
if((Rows 'SELECT DISTINCT `Key` FROM `Registry`') | Where-Object {($_ -join ' ') -match 'RhinoDevSandbox|NativeIsolation|Scheme__'}){throw 'Installer writes sandbox registration.'}
$directory=Rows "SELECT ``Directory``,``Directory_Parent``,``DefaultDir`` FROM ``Directory`` WHERE ``Directory`` = 'INSTALLFOLDER'"
if(-not($directory | Where-Object {$_[0] -eq 'INSTALLFOLDER' -and $_[2] -match '(^|\|)RhinoSceneFlow$'})){throw 'Unexpected install root.'}
$repairMode=Rows "SELECT ``Value`` FROM ``Property`` WHERE ``Property`` = 'REINSTALLMODE'"
if($repairMode.Count -ne 1 -or $repairMode[0][0] -ne 'amus'){throw 'Repair must restore all owned application files.'}
$upgrades=Rows 'SELECT `UpgradeCode` FROM `Upgrade`';if(-not $upgrades.Count){throw 'Upgrade/downgrade rules missing.'}
$actions=Rows 'SELECT `Action` FROM `CustomAction`';if(-not($actions | Where-Object {$_[0] -eq 'CheckEnvironment'})){throw 'Environment guard missing.'}
$files=Rows 'SELECT `FileName` FROM `File`';if($files | Where-Object {$_[0] -match '(?i)(^|\|)(auth\.json|config\.toml|credentials|.*\.3dm|.*\.psd|.*\.pyc)$'}){throw 'Private/test/generated files in installer.'}
$probe=Start-Process -FilePath (Join-Path $output 'SceneFlow.Prerequisites.exe') -ArgumentList '--probe' -WindowStyle Hidden -Wait -PassThru
if($probe.ExitCode -notin 0,10,11){throw 'Read-only native probe failed.'}
$layout=Join-Path $out 'layout-final'
$process=Start-Process -FilePath $exe -ArgumentList @('/layout',('"'+$layout+'"'),'/quiet','/log',('"'+(Join-Path $out 'layout-final.log')+'"')) -WindowStyle Hidden -Wait -PassThru
if($process.ExitCode -ne 0){throw 'EXE layout failed.'}
$laidOut=Join-Path $layout ([IO.Path]::GetFileName($exe))
if(-not(Test-Path -LiteralPath $laidOut) -or (Get-FileHash -LiteralPath $laidOut).Hash -ne (Get-FileHash -LiteralPath $exe).Hash){throw 'Layout bundle mismatch.'}
# Compressed bundles retain payloads inside the laid-out EXE. Extract them read-only
# and compare bytes, rather than expecting an external MSI beside the EXE.
$extract=Join-Path $out 'extract-final'
& (Join-Path $root 'artifacts/installer-tools/wix.exe') burn extract $exe -o $extract *> (Join-Path $out 'extract.log')
if($LASTEXITCODE -ne 0){throw 'Bundle payload extraction failed.'}
$expectedHash=(Get-FileHash -LiteralPath $msi).Hash
$size=(Get-Item -LiteralPath $msi).Length
$candidates=@(Get-ChildItem -LiteralPath $extract -Recurse -File | Where-Object Length -eq $size | Where-Object {(Get-FileHash -LiteralPath $_.FullName).Hash -eq $expectedHash})
if($candidates.Count -ne 1){throw 'Bundled MSI bytes differ from the validated MSI.'}
if((Registration) -ne $before){throw 'Read-only test modified production registration.'}
$result=@{version=$Version;msiTablesPassed=$true;standardRegistrationOnly=$true;upgradeRules=$true;nativeProbeExit=$probe.ExitCode;bundleLayoutPassed=$true;productionRegistrationUnchanged=$true;actuallyInstalled=$false;maintenanceLifecycleTested=$false;fileCount=$files.Count}
$result | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $out 'installer-verified.json') -Encoding UTF8
$result | ConvertTo-Json

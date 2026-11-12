[CmdletBinding()]
param([string]$PackageDirectory,[string]$PublisherThumbprint='',[switch]$SkipRuntimeStage,[string]$BuildPython='')
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
if(-not $PackageDirectory){$PackageDirectory=Join-Path $root 'artifacts/package/RhinoSceneFlow'}
$PackageDirectory=[IO.Path]::GetFullPath($PackageDirectory)
$version=([xml](Get-Content -LiteralPath (Join-Path $root 'Directory.Build.props') -Raw)).Project.PropertyGroup.Version
if($version -notmatch '^\d+\.\d+\.\d+$'){throw 'A three-part version is required.'}
if($PublisherThumbprint -and $PublisherThumbprint -notmatch '^[a-fA-F0-9]{40}$'){throw 'Invalid code-signing certificate thumbprint.'}
$output=Join-Path $root "artifacts/installer/$version"
$payload=Join-Path $output 'payload'
$dependencies=Join-Path $root 'artifacts/installer-dependencies'
$tools=Join-Path $root 'artifacts/installer-tools'
New-Item -ItemType Directory -Force -Path $output,$payload,$dependencies,$tools | Out-Null
$plugin=Join-Path $PackageDirectory 'RhinoSceneFlow.Plugin.rhp'
if([Reflection.AssemblyName]::GetAssemblyName($plugin).Version.ToString(3) -ne $version){throw 'Build scripts/Build.ps1 first; package version differs.'}
if((Get-Content -LiteralPath (Join-Path $PackageDirectory 'PostProduction/version.txt') -Raw).Trim() -ne $version){throw 'Web version differs.'}
# Stage only the curated application, never an arbitrary development output or user data.
foreach($name in @('RhinoSceneFlow.Plugin.rhp','RhinoSceneFlow.rui','RhinoSceneFlow.Plugin.deps.json','RhinoSceneFlow.Core.dll','geometry3Sharp.dll','SceneFlow.UvWorker.exe','Microsoft.Web.WebView2.Core.dll','Microsoft.Web.WebView2.Wpf.dll','geometry3Sharp-LICENSE.txt','xatlas-LICENSE.txt','FastNoiseLite-LICENSE.txt','Lucide-LICENSE.txt')){
    Copy-Item -LiteralPath (Join-Path $PackageDirectory $name) -Destination $payload -Force
}
foreach($folder in @('ChatKit','PostProduction','runtimes')){Copy-Item -LiteralPath (Join-Path $PackageDirectory $folder) -Destination $payload -Recurse -Force}
foreach($notice in @('LICENSE.txt','NOTICE.txt')){Copy-Item -LiteralPath (Join-Path $env:USERPROFILE ".nuget/packages/microsoft.web.webview2/1.0.4314.35/$notice") -Destination (Join-Path $payload "WebView2-$notice") -Force}
& dotnet publish (Join-Path $root 'src/RhinoSceneFlow.TextureWorker/RhinoSceneFlow.TextureWorker.csproj') -c Release -r win-x64 --self-contained true -o (Join-Path $payload 'TextureWorker') -p:DebugType=None -p:DebugSymbols=false *> (Join-Path $output 'texture-publish.log')
if($LASTEXITCODE -ne 0){throw 'Texture worker publish failed; see texture-publish.log.'}
& dotnet publish (Join-Path $root 'src/SceneFlow.Update/SceneFlow.Update.csproj') -c Release -r win-x64 --self-contained true -o (Join-Path $payload 'Updater') -p:DebugType=None -p:DebugSymbols=false *> (Join-Path $output 'updater-publish.log')
if($LASTEXITCODE -ne 0){throw 'Updater publish failed; see updater-publish.log.'}
if(-not $SkipRuntimeStage){
    $ErrorActionPreference='Continue'
    $stageArgs=@('-NoProfile','-ExecutionPolicy','Bypass','-File',(Join-Path $root 'scripts/Stage-ReleaseRuntime.ps1'),'-RuntimeDirectory',(Join-Path $payload 'Runtime'))
    if($BuildPython){$stageArgs+=@('-BuildPython',$BuildPython)}
    & powershell @stageArgs *> (Join-Path $output 'runtime-stage.log')
    $ErrorActionPreference='Stop'
    if($LASTEXITCODE -ne 0){throw 'Private runtime staging failed; see runtime-stage.log.'}
}
$python=Join-Path $payload 'Runtime/Scripts/python.exe'
if(-not(Test-Path -LiteralPath $python)){throw 'Private Python runtime is missing.'}
& $python -I -X utf8 -c 'import chatkit,fastapi,uvicorn,psd_tools,PIL,numpy,cv2,pyvips'
if($LASTEXITCODE -ne 0){throw 'Private runtime is incomplete.'}
# Public distribution notices are app-owned files and must survive repair too.
Copy-Item -LiteralPath (Join-Path $root 'THIRD-PARTY-NOTICES.md') -Destination $payload -Force
Copy-Item -LiteralPath (Join-Path $root 'LICENSE') -Destination $payload -Force
Copy-Item -LiteralPath (Join-Path $root 'docs/Privacy.md') -Destination (Join-Path $payload 'Privacy.md') -Force
$notices=Join-Path $payload 'Notices'
New-Item -ItemType Directory -Force -Path $notices | Out-Null
foreach($folder in @('dotnet','libvips')){
    Copy-Item -LiteralPath (Join-Path $root "third-party/$folder") -Destination $notices -Recurse -Force
}
Copy-Item -LiteralPath (Join-Path $root 'docs/Getting-Started.md') -Destination (Join-Path $payload 'Getting-Started.md') -Force
# Pin the same original McNeel version used by our B regressions, not an untested latest.
$mcpName='rhino-mcp-platform-0.3.0-rh8_19-win.yak'
$mcp=Join-Path $dependencies $mcpName
if(-not(Test-Path -LiteralPath $mcp)){Invoke-WebRequest "https://github.com/mcneel/RhinoAI/releases/download/plugin-v0.3.0/$mcpName" -OutFile $mcp}
if((Get-FileHash -LiteralPath $mcp).Hash -ne '5012B301B104C1154C9CDFC740C38C70A872F39AB42EC35E7C104D7B523BB5E1'){throw 'McNeel package integrity failure.'}
$mcpLicense=Join-Path $dependencies 'RhinoAI-LICENSE.txt'
Invoke-WebRequest 'https://raw.githubusercontent.com/mcneel/RhinoAI/plugin-v0.3.0/LICENSE' -OutFile $mcpLicense
$web=Join-Path $dependencies 'MicrosoftEdgeWebview2Setup.exe'
if(-not(Test-Path -LiteralPath $web)){Invoke-WebRequest 'https://go.microsoft.com/fwlink/p/?LinkId=2124703' -OutFile $web}
$webSignature=Get-AuthenticodeSignature -LiteralPath $web
if($webSignature.Status -ne 'Valid' -or $webSignature.SignerCertificate.Subject -notmatch 'O=Microsoft Corporation'){throw 'WebView2 bootstrapper must have a valid Microsoft signature.'}
Copy-Item -LiteralPath $mcpLicense -Destination $payload -Force
@{schema=1;target='Rhino8-production';version=$version;publisherThumbprint=$PublisherThumbprint.ToUpperInvariant();mcpVersion='0.3.0';preservesUserData=$true} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $payload 'installation.json') -Encoding UTF8
@'
SceneFlow for Rhino 8 — installation preview
Installs for the current Windows user into standard Rhino 8, outside RhinoDevSandbox.
Requires Rhino 8.34+ x64. Save and close standard Rhino before install/repair/uninstall.
Contains original McNeel Rhino MCP Platform 0.3.0 and private Python/runtime dependencies.
If WebView2 is missing, its Microsoft bootstrapper needs Internet access.
AI generation requires the user's own supported Codex installation, ChatGPT login and image access.
Repair/uninstall do not delete user materials, plants, boards or shared MCP/WebView2.
Legacy Yak/manual SceneFlow registrations must be removed before this MSI-managed installation.
This preview has NOT passed clean-machine installation/repair/uninstall acceptance.
Third-party licenses/notices accompany their binaries, Python distributions and browser vendors.
'@ | Set-Content -LiteralPath (Join-Path $payload 'Installation-Readme.txt') -Encoding UTF8
if(-not(Test-Path -LiteralPath (Join-Path $tools 'wix.exe'))){& dotnet tool install wix --version 5.0.2 --tool-path $tools;if($LASTEXITCODE -ne 0){throw 'WiX install failed.'}}
& (Join-Path $tools 'wix.exe') extension add -g WixToolset.BootstrapperApplications.wixext/5.0.2 *> (Join-Path $output 'wix-extension.log')
if($LASTEXITCODE -ne 0){throw 'WiX bootstrapper extension failed.'}
$vswhere='C:/Program Files (x86)/Microsoft Visual Studio/Installer/vswhere.exe'
$vs=& $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
Import-Module (Join-Path $vs 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')
Enter-VsDevShell -VsInstallPath $vs -SkipAutomaticLocation -DevCmdArguments '-arch=amd64 -host_arch=amd64' | Out-Null
Push-Location $output
try{
    & cl /nologo /utf-8 /std:c++17 /EHsc /MT /W4 /DUNICODE /D_UNICODE /LD (Join-Path $root 'installer/native/InstallGuard.cpp') msi.lib shell32.lib ole32.lib version.lib advapi32.lib /link /OUT:InstallGuard.dll *> guard-build.log
    if($LASTEXITCODE -ne 0){throw 'Install guard build failed.'}
    & cl /nologo /utf-8 /std:c++17 /EHsc /MT /W4 /DUNICODE /D_UNICODE (Join-Path $root 'installer/native/Prerequisites.cpp') shell32.lib user32.lib ole32.lib version.lib advapi32.lib /link /SUBSYSTEM:WINDOWS /OUT:SceneFlow.Prerequisites.exe *> prerequisites-build.log
    if($LASTEXITCODE -ne 0){throw 'Prerequisites build failed.'}
}finally{Pop-Location}
function StableGuid([string]$Text){$md5=[Security.Cryptography.MD5]::Create();try{return [guid]::new($md5.ComputeHash([Text.Encoding]::UTF8.GetBytes($Text)))}finally{$md5.Dispose()}}
function StableId([string]$Text){return 'f'+(StableGuid $Text).ToString('N')}
$ns='http://wixtoolset.org/schemas/v4/wxs'
$document=[xml]"<Wix xmlns='$ns'><Fragment><ComponentGroup Id='ApplicationFiles'/></Fragment></Wix>"
$fragment=$document.DocumentElement.FirstChild;$group=$fragment.FirstChild
function Node($Parent,$Name,$Attributes){$n=$document.CreateElement($Name,$ns);foreach($entry in $Attributes.GetEnumerator()){$n.SetAttribute($entry.Key,[string]$entry.Value)};$Parent.AppendChild($n)|Out-Null;return $n}
$directories=@{''='INSTALLFOLDER'}
foreach($file in Get-ChildItem -LiteralPath $payload -Recurse -File | Sort-Object FullName){
    if($file.Extension -in '.pdb','.pyc'){continue}
    if(($file.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){throw 'Installer input must not contain reparse points.'}
    $relative=$file.FullName.Substring($payload.Length+1);$folder=[IO.Path]::GetDirectoryName($relative);$parent='INSTALLFOLDER';$current=''
    if($folder){foreach($part in $folder.Split('\')){$current=if($current){$current+'\'+$part}else{$part};if(-not $directories.ContainsKey($current)){$id=StableId ('dir:'+ $current);$ref=Node $fragment 'DirectoryRef' @{Id=$parent};Node $ref 'Directory' @{Id=$id;Name=$part}|Out-Null;$directories[$current]=$id};$parent=$directories[$current]}}
    $id=StableId ('file:'+ $relative);$ref=Node $fragment 'DirectoryRef' @{Id=$parent};$component=Node $ref 'Component' @{Id=$id;Guid=(StableGuid ('SceneFlow-file:'+ $relative.ToLowerInvariant()))}
    Node $component 'File' @{Id=('p'+$id);Source=$file.FullName;Name=$file.Name}|Out-Null
    Node $component 'RegistryValue' @{Root='HKCU';Key='Software\SceneFlow\Installer\Files';Name=$id;Type='integer';Value=1;KeyPath='yes'}|Out-Null
    Node $group 'ComponentRef' @{Id=$id}|Out-Null
}
$document.Save((Join-Path $output 'Files.wxs'))
$msi=Join-Path $output "SceneFlow-$version-win-x64.msi"
& (Join-Path $tools 'wix.exe') build (Join-Path $root 'installer/Package.wxs') (Join-Path $output 'Files.wxs') -arch x64 -d "Version=$version" -d "ProductCode=$(StableGuid ('SceneFlow-MSI-'+$version))" -d "Guard=$(Join-Path $output 'InstallGuard.dll')" -o $msi *> (Join-Path $output 'msi-build.log')
if($LASTEXITCODE -ne 0){throw 'MSI build failed; see msi-build.log.'}
$exe=Join-Path $output "SceneFlow-Setup-$version-win-x64.exe"
& (Join-Path $tools 'wix.exe') build (Join-Path $root 'installer/Bundle.wxs') -arch x64 -ext WixToolset.BootstrapperApplications.wixext/5.0.2 -d "Version=$version" -d "ReleasePage=https://github.com/baoying-liu/RhinoSceneFlow/releases" -d "Prerequisites=$(Join-Path $output 'SceneFlow.Prerequisites.exe')" -d "McpPackage=$mcp" -d "McpLicense=$mcpLicense" -d "WebViewInstaller=$web" -d "Msi=$msi" -o $exe *> (Join-Path $output 'bundle-build.log')
if($LASTEXITCODE -ne 0){throw 'EXE bundle build failed; see bundle-build.log.'}
if($PublisherThumbprint){
    $signtool=Get-ChildItem 'C:/Program Files (x86)/Windows Kits/10/bin/*/x64/signtool.exe' | Sort-Object FullName -Descending | Select-Object -First 1
    & $signtool.FullName sign /sha1 $PublisherThumbprint /fd SHA256 /tr 'http://timestamp.digicert.com' /td SHA256 $exe
    if($LASTEXITCODE -ne 0){throw 'Installer signing failed.'}
    if((Get-AuthenticodeSignature -LiteralPath $exe).Status -ne 'Valid'){throw 'Installer signature validation failed.'}
}
@{version=$version;exe=$exe;msi=$msi;sha256=(Get-FileHash -LiteralPath $exe).Hash;productionInstalled=$false;signed=[bool]$PublisherThumbprint;cleanMachineValidated=$false;target='standard Rhino 8; not sandbox';mcpSha256=(Get-FileHash -LiteralPath $mcp).Hash} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $output 'receipt.json') -Encoding UTF8
Write-Output "Built installer (not installed): $exe"

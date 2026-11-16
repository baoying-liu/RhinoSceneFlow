$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$out=Join-Path $root 'artifacts/installer-paths'
New-Item -ItemType Directory -Force $out | Out-Null
$vs=& 'C:/Program Files (x86)/Microsoft Visual Studio/Installer/vswhere.exe' -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
Import-Module (Join-Path $vs 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')
Enter-VsDevShell -VsInstallPath $vs -SkipAutomaticLocation -DevCmdArguments '-arch=amd64 -host_arch=amd64' | Out-Null
@'
#include "Environment.h"
#include <cassert>
int main() {
    auto root=L"C:\\Users\\Test\\AppData\\Local\\Programs/SceneFlow";
    assert(IsManagedPluginPath(L"c:/users/test/AppData/Local/Programs/SceneFlow/RhinoSceneFlow.Plugin.rhp",root));
    assert(IsManagedPluginPath(L"C:\\Users\\Test\\AppData\\Local\\Programs\\SceneFlow\\RhinoSceneFlow.Plugin.rhp",root));
    assert(!IsManagedPluginPath(L"C:\\Users\\Test\\AppData\\Local\\Programs\\SceneFlowOther\\RhinoSceneFlow.Plugin.rhp",root));
    assert(!IsManagedPluginPath(L"C:\\Users\\Test\\AppData\\Local\\Programs\\SceneFlow\\..\\manual\\RhinoSceneFlow.Plugin.rhp",root));
    assert(!IsManagedPluginPath(L"D:\\Manual\\RhinoSceneFlow.Plugin.rhp",root));
    assert(!IsManagedPluginPath(L"",root));
}
'@ | Set-Content (Join-Path $out 'paths.cpp') -Encoding UTF8
Push-Location $out
try {
    & cl /nologo /std:c++17 /EHsc /MT /W4 /DUNICODE /D_UNICODE "/I$root/installer/native" paths.cpp /Fe:paths.exe *> build.log
    if($LASTEXITCODE -ne 0){throw 'Native path regression compilation failed.'}
    & ./paths.exe
    if($LASTEXITCODE -ne 0){throw 'Native path regression failed.'}
} finally {Pop-Location}
Write-Output 'PASS: managed installer paths normalize slash/case, preserve directory boundary and reject manual/sibling paths. No registry writes or installation.'

#include "Environment.h"
#include <shellapi.h>
#include <fstream>

int WINAPI wWinMain(HINSTANCE,HINSTANCE,PWSTR,int) {
    int argc{};auto argv=CommandLineToArgvW(GetCommandLineW(),&argc);
    bool probe=argc>1&&std::wstring(argv[1])==L"--probe";LocalFree(argv);
    // A read-only probe is used by the test harness; never installs or changes registration.
    if(probe)return SupportedRhino()?(HasProductionRhino()?10:0):11;
    if(!SupportedRhino()||HasProductionRhino()||HasOwnedPython()) {
        MessageBoxW(nullptr,L"Install Rhino 8.34+ and close standard Rhino before continuing. Sandbox B can remain open. / 请先安装 Rhino 8.34+ 并保存关闭正式 Rhino。",L"SceneFlow Setup",MB_OK|MB_ICONERROR);return 1603;
    }
    wchar_t self[32768]{};GetModuleFileNameW(nullptr,self,32768);auto root=std::filesystem::path(self).parent_path();
    // Bundle the original, pinned McNeel Yak; run the user's original Yak outside any sandbox.
    auto mcpRoot=std::filesystem::path(KnownFolder(FOLDERID_RoamingAppData))/L"McNeel/Rhinoceros/packages/8.0/Rhino-MCP-Platform";
    bool mcpReady=false;
    if(std::filesystem::exists(mcpRoot))for(const auto& entry:std::filesystem::directory_iterator(mcpRoot)) {
        if(!entry.is_directory())continue;
        unsigned major{},minor{},patch{};wchar_t tail{};auto name=entry.path().filename().wstring();
        if(swscanf_s(name.c_str(),L"%u.%u.%u%c",&major,&minor,&patch,&tail,1)!=3)continue;
        if(major==0&&minor<3)continue;
        for(const auto& file:std::filesystem::recursive_directory_iterator(entry.path()))if(file.path().extension()==L".rhp")mcpReady=true;
    }
    if(!mcpReady) {
        auto code=Run((std::filesystem::path(RhinoSystem())/L"Yak.exe").wstring(),{L"install",(root/L"rhino-mcp-platform-0.3.0-rh8_19-win.yak").wstring()});
        if(code)return static_cast<int>(code);
    }
    // Prefer a machine's existing Evergreen runtime. Install Microsoft's original bootstrapper only if absent.
    const wchar_t* key=L"Software\\Microsoft\\EdgeUpdate\\Clients\\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}";
    auto web=RegistryString(HKEY_CURRENT_USER,key,L"pv");
    if(web.empty())web=RegistryString(HKEY_LOCAL_MACHINE,key,L"pv");
    if(web.empty())web=RegistryString(HKEY_LOCAL_MACHINE,L"Software\\WOW6432Node\\Microsoft\\EdgeUpdate\\Clients\\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}",L"pv");
    if(web.empty()||web==L"0.0.0.0") {
        auto code=Run((root/L"MicrosoftEdgeWebview2Setup.exe").wstring(),{L"/silent",L"/install"});
        if(code&&code!=3010)return static_cast<int>(code);
    }
    return 0;
}

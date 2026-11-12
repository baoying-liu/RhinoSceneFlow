#pragma once
#include <windows.h>
#include <tlhelp32.h>
#include <shlobj.h>
#include <string>
#include <vector>
#include <filesystem>
#include <algorithm>
#include <cwctype>

inline std::wstring Lower(std::wstring s) { std::transform(s.begin(),s.end(),s.begin(),::towlower);return s; }
inline std::wstring KnownFolder(REFKNOWNFOLDERID id) {
    PWSTR p{};if(FAILED(SHGetKnownFolderPath(id,0,nullptr,&p)))return L"";
    std::wstring s(p);CoTaskMemFree(p);return s;
}
inline std::wstring RegistryString(HKEY root,const wchar_t* key,const wchar_t* name) {
    wchar_t text[32768]{};DWORD size=sizeof(text);
    if(RegGetValueW(root,key,name,RRF_RT_REG_SZ|RRF_SUBKEY_WOW6464KEY,nullptr,text,&size)!=ERROR_SUCCESS)return L"";
    return text;
}
inline std::wstring RhinoSystem() {
    auto path=RegistryString(HKEY_LOCAL_MACHINE,L"SOFTWARE\\McNeel\\Rhinoceros\\8.0\\Install",L"Path");
    if(path.empty())path=KnownFolder(FOLDERID_ProgramFiles)+L"\\Rhino 8\\System";
    return path;
}
inline bool SupportedRhino() {
    auto file=(std::filesystem::path(RhinoSystem())/L"RhinoCommon.dll").wstring();DWORD unused{};
    DWORD size=GetFileVersionInfoSizeW(file.c_str(),&unused);if(!size)return false;
    std::vector<BYTE> bytes(size);if(!GetFileVersionInfoW(file.c_str(),0,size,bytes.data()))return false;
    VS_FIXEDFILEINFO* info{};UINT length{};
    if(!VerQueryValueW(bytes.data(),L"\\",reinterpret_cast<void**>(&info),&length)||!info)return false;
    return HIWORD(info->dwFileVersionMS)==8 && LOWORD(info->dwFileVersionMS)>=34;
}
inline bool HasProductionRhino() {
    HANDLE snap=CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS,0);if(snap==INVALID_HANDLE_VALUE)return true;
    PROCESSENTRY32W row{sizeof(row)};bool blocked=false;
    if(Process32FirstW(snap,&row)) do {
        if(Lower(row.szExeFile)!=L"rhino.exe")continue;
        HANDLE modules=CreateToolhelp32Snapshot(TH32CS_SNAPMODULE|TH32CS_SNAPMODULE32,row.th32ProcessID);
        if(modules==INVALID_HANDLE_VALUE){blocked=true;break;}
        MODULEENTRY32W module{sizeof(module)};bool isolated=false,read=false;
        if(Module32FirstW(modules,&module))do {read=true;if(Lower(module.szModule)==L"rhinodevsandbox.registry64.dll")isolated=true;}while(Module32NextW(modules,&module));
        CloseHandle(modules);if(!read||!isolated){blocked=true;break;}
    }while(Process32NextW(snap,&row));
    CloseHandle(snap);return blocked;
}
inline bool HasOwnedPython() {
    auto prefix=Lower((std::filesystem::path(KnownFolder(FOLDERID_LocalAppData))/L"Programs/RhinoSceneFlow").wstring())+L"\\";
    HANDLE snap=CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS,0);if(snap==INVALID_HANDLE_VALUE)return true;
    PROCESSENTRY32W row{sizeof(row)};bool blocked=false;
    if(Process32FirstW(snap,&row))do {
        if(Lower(row.szExeFile)!=L"python.exe" && Lower(row.szExeFile)!=L"sceneflow.textureworker.exe")continue;
        HANDLE process=OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION,FALSE,row.th32ProcessID);if(!process)continue;
        wchar_t path[32768]{};DWORD length=32768;
        if(QueryFullProcessImageNameW(process,0,path,&length)&&Lower(path).rfind(prefix,0)==0)blocked=true;
        CloseHandle(process);if(blocked)break;
    }while(Process32NextW(snap,&row));
    CloseHandle(snap);return blocked;
}
inline std::wstring Quote(const std::wstring& arg) {
    std::wstring result=L"\"";size_t slashes=0;
    for(auto c:arg){if(c==L'\\'){++slashes;continue;}result.append(c==L'\"'?slashes*2+1:slashes,L'\\');result+=c;slashes=0;}
    result.append(slashes*2,L'\\');return result+L"\"";
}
inline DWORD Run(const std::wstring& file,const std::vector<std::wstring>& args) {
    auto command=Quote(file);for(const auto& arg:args)command+=L" "+Quote(arg);
    STARTUPINFOW startup{sizeof(startup)};startup.dwFlags=STARTF_USESHOWWINDOW;startup.wShowWindow=SW_HIDE;
    PROCESS_INFORMATION process{};
    if(!CreateProcessW(file.c_str(),command.data(),nullptr,nullptr,FALSE,CREATE_NO_WINDOW,nullptr,nullptr,&startup,&process))return GetLastError();
    WaitForSingleObject(process.hProcess,INFINITE);DWORD code{};GetExitCodeProcess(process.hProcess,&code);
    CloseHandle(process.hProcess);CloseHandle(process.hThread);return code;
}

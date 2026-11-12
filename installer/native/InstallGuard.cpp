#include "Environment.h"
#include <msiquery.h>

static UINT Fail(MSIHANDLE install,const wchar_t* text) {
    auto record=MsiCreateRecord(0);MsiRecordSetStringW(record,0,text);MsiProcessMessage(install,INSTALLMESSAGE_ERROR,record);MsiCloseHandle(record);return ERROR_INSTALL_FAILURE;
}
extern "C" __declspec(dllexport) UINT __stdcall CheckEnvironment(MSIHANDLE install) {
    if(HasProductionRhino())return Fail(install,L"Save your models and close standard Rhino before installation, repair or uninstall. Isolated RhinoDevSandbox sessions may remain open. / 请先保存并关闭正式 Rhino；不强制关闭进程。");
    if(HasOwnedPython())return Fail(install,L"Close SceneFlow Web Studio using its Stop service action before continuing. / 请先在正式版 Web 工作台中关闭服务，再继续。不会终止其他 Python 进程。");
    wchar_t remove[32]{};DWORD length=32;MsiGetPropertyW(install,L"REMOVE",remove,&length);
    if(remove[0])return ERROR_SUCCESS;
    if(!SupportedRhino())return Fail(install,L"Rhino 8.34 or newer (Rhino 8, Windows x64) is required. / 需要 Rhino 8.34 或更新的 Rhino 8。");
    auto packages=std::filesystem::path(KnownFolder(FOLDERID_RoamingAppData))/L"McNeel/Rhinoceros/packages/8.0/rhinosceneflow";
    if(std::filesystem::exists(packages))return Fail(install,L"A previous Yak installation of SceneFlow was found. Remove only RhinoSceneFlow in Rhino PackageManager, close Rhino, then run this installer again. Libraries and boards are retained. / 检测到旧 Yak 安装，请先在 PackageManager 卸载 RhinoSceneFlow（保留个人数据）。");
    auto expected=Lower((std::filesystem::path(KnownFolder(FOLDERID_LocalAppData))/L"Programs/RhinoSceneFlow").wstring());
    for(auto hive:{HKEY_CURRENT_USER,HKEY_LOCAL_MACHINE}) {
        auto registered=Lower(RegistryString(hive,L"Software\\McNeel\\Rhinoceros\\8.0\\Plug-ins\\8b902013-73dd-4227-b45b-896f6a33f134",L"FileName"));
        if(registered.empty())registered=Lower(RegistryString(hive,L"Software\\McNeel\\Rhinoceros\\8.0\\Plug-ins\\8b902013-73dd-4227-b45b-896f6a33f134\\PlugIn",L"FileName"));
        if(!registered.empty()&&registered.rfind(expected+L"\\",0)!=0)return Fail(install,L"A manually registered SceneFlow plugin was found. Unregister that copy in Rhino PlugInManager before installing. Do not remove RhinoDevSandbox. / 检测到手动注册的旧插件，请先在正式 Rhino 插件管理器移除该注册。");
    }
    return ERROR_SUCCESS;
}

using System.Diagnostics;
using Eto.Forms;
using RhinoSceneFlow.Core;

namespace RhinoSceneFlow.Plugin;

internal sealed class ConnectionsSettings : Panel
{
    private readonly UiLabel environment = ToolUi.Note(""), account = ToolUi.Note(""), update = ToolUi.Note(""), error = ToolUi.Note("");
    private readonly UiCheckBox automatic = new();
    private readonly UiButton login, device, check, download, install;
    private readonly UITimer timer = new() { Interval = 1 };
    private string T(string zh, string en) => PluginPreferences.Load().ResolvedLanguage == "en" ? en : zh;
    internal ConnectionsSettings()
    {
        var content = Ui.Layout();
        content.AddRow(ToolUi.Note(T("安装目标：正式 Rhino；沙盒通道使用独立部署。", "Install target: standard Rhino. Sandbox channels use isolated deployments.")));
        content.AddRow(environment);
        content.AddRow(Ui.Button(T("检测环境与登录", "Check environment and sign-in"), () => Run(ConnectionService.CheckAsync)));
        content.AddRow(ToolUi.Heading(T("AI 账号", "AI account")));
        content.AddRow(account);
        login = Ui.Button(T("浏览器登录", "Sign in with browser"), () => Run(() => ConnectionService.LoginAsync(false)));
        device = Ui.Button(T("设备码登录", "Sign in with device code"), () => Run(() => ConnectionService.LoginAsync(true)));
        content.AddRow(login); content.AddRow(device);
        content.AddRow(Ui.Button(T("打开设备授权网页", "Open device authorization page"), () => Open("https://auth.openai.com/codex/device")));
        content.AddRow(Ui.Button(T("取消登录", "Cancel sign-in"), ConnectionService.CancelLogin));
        content.AddRow(Ui.Button(T("安装 Codex 说明", "Codex installation guide"), () => Open("https://developers.openai.com/codex/cli/")));
        content.AddRow(ToolUi.Note(T("使用本机 Codex 的正式授权；不读取 ChatGPT 桌面登录缓存。登录成功不保证生图权限或剩余额度。", "Uses supported local Codex authorization; never reads ChatGPT desktop credentials. Sign-in does not guarantee image access or remaining quota.")));
        content.AddRow(ToolUi.Heading(T("Rhino MCP", "Rhino MCP")));
        content.AddRow(ToolUi.Note(T("依赖 McNeel 原厂 Rhino MCP Platform。先安装并启动 Platform，再按官方说明把客户端连接到它的实际地址。沙盒管理端口不是发布版 MCP 地址。", "Requires McNeel's original Rhino MCP Platform. Install and start Platform, then connect your client to its actual address using the official guide. Sandbox management ports are not production MCP addresses.")));
        content.AddRow(Ui.Button(T("原厂 MCP 配置说明", "Official MCP configuration guide"), () => Open("https://mcneel.github.io/RhinoAI/docs/getting-started/")));
        content.AddRow(ToolUi.Heading(T("软件更新", "Software updates")));
        automatic.Text = T("启动时自动检查新版", "Check for updates on startup"); automatic.Checked = ReleaseService.AutoCheck;
        automatic.CheckedChanged += (_, _) => { try { ReleaseService.AutoCheck = automatic.Checked == true; } catch (Exception e) { error.Text = e.Message; } };
        content.AddRow(automatic); content.AddRow(update);
        check = Ui.Button(T("检查更新", "Check for updates"), () => Run(ReleaseService.CheckAsync));
        download = Ui.Button(T("下载并校验更新", "Download and verify update"), () => Run(ReleaseService.DownloadAsync));
        install = Ui.Button(T("保存并关闭 Rhino 以更新", "Save and close Rhino to update"), () => Run(ReleaseService.InstallAfterExitAsync));
        content.AddRow(check); content.AddRow(download); content.AddRow(install);
        content.AddRow(Ui.Button(T("查看发行版本", "View releases"), () => Open(ReleaseFeed.ReleasesPage)));
        content.AddRow(ToolUi.Note(T("退出时仍由 Rhino 询问是否保存。取消退出不会强制关闭。更新和卸载保留素材库、画板与账号授权。", "Rhino still asks whether to save on exit; cancelling never forces it closed. Updates and uninstall retain libraries, boards and account authorization.")));
        content.AddRow(error); Content = content;
        timer.Elapsed += (_, _) => RefreshSafely();
        if (RefreshSafely()) timer.Start();
    }
    private bool RefreshSafely()
    {
        try { Refresh(); return true; }
        catch (Exception e)
        {
            // Optional diagnostics must never escape a native UI timer into Rhino.
            timer.Stop();
            if (!IsDisposed) error.Text = T("环境检测不可用；其他设置仍可使用。", "Environment detection is unavailable; other settings remain usable.") + " " + e.GetType().Name;
            return false;
        }
    }
    private void Refresh()
    {
        if (IsDisposed) return;
        using var state = System.Text.Json.JsonDocument.Parse(System.Text.Json.JsonSerializer.Serialize(ConnectionService.Inspect()));
        bool Flag(string name) => state.RootElement.GetProperty(name).GetBoolean();
        string Yes(bool value) => value ? T("就绪", "Ready") : T("未就绪", "Not ready");
        environment.Text = (InstallationContext.Sandbox ? T("当前：沙盒（禁止正式安装与更新）", "Current: sandbox (production installation/update disabled)") : InstallationContext.Managed ? T("当前：正式安装", "Current: managed installation") : T("当前：开发／手动安装", "Current: development/manual installation")) + "\n" +
            T("MCP 已加载：", "MCP loaded: ") + Yes(Flag("platformLoaded")) + "\n" + T("Python 环境：", "Python runtime: ") + (ConnectionService.Runtime == "ready" ? T("依赖导入通过", "Dependency imports passed") : ConnectionService.Runtime == "not_checked" ? T("尚未检测", "Not checked") : T("需检测或修复", "Check or repair required")) + "\n" + "WebView2: " + Yes(Flag("webViewInstalled"));
        string auth = ConnectionService.Auth switch
        {
            "chatgpt" => T("已通过 ChatGPT 登录 Codex", "Codex signed in with ChatGPT"),
            "api_key" => T("检测到 API Key 登录；当前生图流程需要 ChatGPT 登录", "API-key sign-in detected; current image workflow requires ChatGPT sign-in"),
            "signed_out" => T("尚未登录", "Signed out"), "missing" => T("尚未安装 Codex", "Codex is not installed"),
            "signing_in" => T("等待浏览器／设备码授权", "Waiting for browser/device authorization"),
            "cancelled" => T("登录已取消或超时", "Sign-in cancelled or timed out"),
            "timeout" => T("登录检测超时，可重试", "Sign-in check timed out; retry"),
            "failed" => T("连接失败，可重试登录", "Connection failed; retry sign-in"),
            _ => T("登录状态尚未检测", "Sign-in has not been checked")
        };
        account.Text = auth + (ConnectionService.DeviceCode.Length > 0 ? "\n" + T("设备码：", "Device code: ") + ConnectionService.DeviceCode : "");
        update.Text = "SceneFlow " + typeof(ConnectionsSettings).Assembly.GetName().Version!.ToString(3) + "\n" + (ReleaseService.Status switch
        {
            "checking" => T("正在检查 GitHub 发行版本…", "Checking GitHub releases…"), "current" => T("已是最新公开稳定版", "Up to date with public stable releases"),
            "available" => T("发现新版：", "Update available: ") + ReleaseService.Offer?.Version,
            "not_public" => T("仓库尚未公开，或尚无公开稳定版；不影响当前使用。", "Repository is private or has no public stable release; current use is unaffected."),
            "rate_limit" => T("GitHub 请求受限，请稍后重试。", "GitHub rate limit reached; try later."),
            "offline" => T("无法连接更新服务，请检查网络后重试。", "Update service unavailable; check your network and retry."),
            "downloading" => T("正在下载和校验安装包…", "Downloading and verifying installer…"), "ready" => T("安装包已校验，可退出后安装。", "Installer verified; ready to install after exit."),
            "download_failed" => T("下载或校验失败，旧版本未修改。", "Download or verification failed; installed version unchanged."),
            _ => T("尚未检查更新", "Updates have not been checked")
        });
        if (InstallationContext.Managed && InstallationContext.PublisherThumbprint.Length == 0) update.Text += "\n" + T("此安装包尚未配置发布者签名，自动安装暂不可用。", "Publisher signing is not configured in this build; automatic installation is unavailable.");
        login.Enabled = device.Enabled = !ConnectionService.Busy;
        check.Enabled = !ReleaseService.Busy;
        download.Enabled = !ReleaseService.Busy && ReleaseService.Offer?.Sha256 is not null && InstallationContext.Managed && InstallationContext.PublisherThumbprint.Length > 0;
        install.Enabled = !ReleaseService.Busy && ReleaseService.Download is not null && InstallationContext.Managed;
    }
    private async void Run(Func<Task> action)
    {
        error.Text = "";
        try { await action(); }
        catch (Exception e) { if (!IsDisposed) error.Text = T("未完成：", "Not completed: ") + e.Message; }
        finally { if (!IsDisposed) RefreshSafely(); }
    }
    private static void Open(string url) { using var child = Process.Start(new ProcessStartInfo(url) { UseShellExecute = true }); }
    protected override void Dispose(bool disposing) { if (disposing) { timer.Stop(); timer.Dispose(); } base.Dispose(disposing); }
}

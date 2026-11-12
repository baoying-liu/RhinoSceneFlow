# SceneFlow 0.23.1 — first public preview

Rhino → AI materials / physical UV → planting → layered PSD → Web AI postproduction.

## 下载与安装 / Download and install

Download **SceneFlow-Setup-0.23.1-win-x64.exe** below. GitHub's automatically generated
source ZIP is not the installer. Compare its SHA-256 with **SHA256SUMS.txt**.

需要 Windows x64、已授权的 **Rhino 8.34+（Rhino 8）和 .NET 8 模式**。
先保存并关闭正式 Rhino，再运行 EXE；安装到当前用户的正式 Rhino，不是沙盒 B。
旧 ZIP／Yak／手动版 SceneFlow 请先移除旧插件注册，保留素材和工程。

Run **`RhinoSceneFlow`** after installation. The environment/sign-in check runs on
startup. If verification fails, use **Go to settings / 前往设置** in the chat area.
Your own Codex CLI installation, ChatGPT sign-in, Internet and image access/quota
are required for AI. The installer does not include an AI subscription. The local
Web workbench uses the same Codex authorization.

[完整安装说明 / Installation guide](https://github.com/baoying-liu/RhinoSceneFlow/blob/master/docs/Getting-Started.md)

## Included / 主要功能

- AI 材质与透明植物素材、已有素材检索、本地共享素材库。
- 真实尺寸 UV、xatlas 复杂网格展开、材质应用与去重复。
- 参数化种植组合、Plants List、季节与相机跟随显示。
- Named Views 批量分层 PSD：材质、植物、阴影、极地模式、深度等通道。
- Web 列表／画布、标注、父子图溯源、PhotoCraft 参考编辑层、整图探索与高清处理。
- Dockable native tools, English/Chinese UI and original McNeel MCP automation.
- EXE packaging with private runtimes, startup verification and repair/uninstall UI.

## Preview limitations / 测试版限制

- **Unsigned / 未签名。** Windows cannot verify the publisher. Automatic installation
  of updates is disabled; later previews require manual installation. Do not disable
  security protections for unexpected or mismatched downloads.
- **Not stable / 非正式稳定版。** Clean-machine install, repair, uninstall,
  cross-version upgrade/rollback and a fresh recipient account login have not
  completed acceptance. These are known validation gaps, not passing tests.
- Existing sandbox B feature checks, native/core regressions, actual private-runtime
  workflow tests and read-only MSI/extraction checks have passed. No production Rhino
  installation was performed as part of these checks.
- Legacy Yak/manual installs are detected and blocked with removal instructions;
  automatic migration is not implemented. Back up libraries, boards and models.
- No promise of model-perfect AI geometry, globally seamless UV or unrestricted
  material/renderer compatibility. Start with a copied scene and low-resolution output.
- Application uninstall is designed to retain user materials, plants, boards,
  authorization and shared MCP/WebView2; the full maintenance lifecycle remains unverified.

## Dependencies / 依赖

Bundled original McNeel Rhino MCP Platform 0.3.0, private CPython and image libraries,
.NET worker runtimes and Microsoft's original WebView2 bootstrapper. WebView2 needs
Internet if absent. Source/build material for libvips and its dependencies is supplied
in **SceneFlow-ThirdParty-Sources-0.23.1.zip**; normal users need only the EXE.

[Third-party notices and project licensing status](https://github.com/baoying-liu/RhinoSceneFlow/blob/master/THIRD-PARTY-NOTICES.md).
No open-source license for SceneFlow's own original code is selected in this preview;
the explicit third-party licenses remain in effect.

Please report reproducible problems in [Issues](https://github.com/baoying-liu/RhinoSceneFlow/issues).
Include versions and sanitized screenshots, never authentication files, bearer URLs
or confidential project assets.

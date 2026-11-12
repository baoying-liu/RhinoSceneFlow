# SceneFlow for Rhino 8

**First public preview · 0.23.1 · Windows x64 · Rhino 8.34+ / .NET 8**

AI assets → physical-scale materials and UV → planting → layered PSD → AI postproduction.

[Download the preview](https://github.com/baoying-liu/RhinoSceneFlow/releases/tag/v0.23.1-preview.1) · [Install / 安装说明](docs/Getting-Started.md) · [Report an issue](https://github.com/baoying-liu/RhinoSceneFlow/issues)

## 中文

SceneFlow 将 AI 素材、真实尺寸材质与 UV、参数化植物布置、多视图 PSD 导出和 Web AI 后期串联起来。
在 Rhino 输入 **`RhinoSceneFlow`** 打开可停靠工作区。界面支持中文和英文。

- 材质与植物：文本／图片参考、优先检索已有素材、本地共享库、分类与标签。
- 真实尺寸 UV：应用材质时自动检查，也可独立展开；复杂曲面使用 xatlas。
- 种植：混合植物组合、密度、独立随机 Seed、曲面附着、季节和平面／立面跟随相机。
- PSD：Named Views、分辨率、材质贴图／颜色、阴影、植物、极地模式和深度图等通道。
- Web：PSD 导入、列表与画布、可追溯子图、标注／参考图、PhotoCraft 编辑参考层、整图与高清处理。

**这是测试版。** EXE 未签名，尚未完成干净电脑的首次安装、修复、卸载及跨版本升级验收。
自动安装更新未启用。请备份工程，从小模型和低分辨率开始，不要直接依赖它完成不可替代的生产工作。
AI 需要另行安装 Codex、使用自己的账号登录，并具有生图权限和额度；安装包不含 AI 订阅。
旧 ZIP／Yak／手动安装的 SceneFlow 需要先移除旧插件注册，保留素材库。

## English

SceneFlow connects AI-assisted asset creation, physically scaled materials, UV preparation,
parametric planting, layered view export and a local browser postproduction workbench.
Run **`RhinoSceneFlow`** in Rhino to open the dockable tools.

Download the **EXE from Releases**, rather than GitHub's source ZIP, for installation.
The installer targets standard Rhino 8 for the current Windows user; it does not install
into RhinoDevSandbox B. Python/image runtimes and original McNeel MCP are bundled.
AI requires a separately installed Codex CLI, your own supported sign-in and image access.

This is an **unsigned public preview**, not a stable production release. Clean-machine
installation, repair, uninstall, cross-version upgrade and new-recipient authorization
remain unverified. Automatic update installation is disabled. Back up user work and
read the [installation guide and limitations](docs/Getting-Started.md).

## Documentation

- [Installation and first workflow](docs/Getting-Started.md)
- [Workspace](docs/Workspace.md) · [Materials and UV](docs/Materials.md)
- [Plant groups](docs/PlantGroups.md) · [PSD workbench](docs/Workbench.md)
- [Studio workflow](docs/Studio.md) · [MCP automation API](docs/MCP.md)
- [Installer architecture and remaining acceptance gates](docs/Release-Installer.md)
- [Third-party notices and licensing status](THIRD-PARTY-NOTICES.md) · [Security/privacy](SECURITY.md)
- [Development validation evidence](docs/Validation.md) · [Historical README](docs/README-History.md)

No open-source license has yet been selected for SceneFlow's own original code.
Publishing source is not an implicit MIT/Apache grant. Third-party components retain
their explicit licenses and notices. SceneFlow is independent of McNeel, OpenAI,
Microsoft and the PhotoCraft authors.

## Build

Requires .NET 8+ SDK, Rhino 8.34+, Node.js with the locked Web dependencies installed,
and the Windows C++ build tools for native workers / the installer. Use:

```powershell
cd web/postproduction
npm ci
cd ../..
./scripts/Build.ps1
./scripts/Build-Installer.ps1
./scripts/Test-Installer.ps1 -Version 0.23.1
```

The installer also needs the pinned embedded Python archive, pip wheel and runtime
inputs described in [Release-Installer.md](docs/Release-Installer.md) and its staging
script. They are build artifacts, not user authentication or personal libraries.
A normal code build does not install into or restart a running Rhino session.

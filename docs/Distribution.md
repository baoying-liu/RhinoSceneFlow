# Windows 测试版分发（0.16.4）

发送 `artifacts/releases/RhinoSceneFlow-0.16.4-Windows-x64.zip`，约 101 MiB。完整解压后运行 Install.cmd，再启动 Rhino 输入 RhinoSceneFlow。要求 Windows x64、Rhino 8.34+ / .NET 8；AI 生成功能另需接收者自己的 Codex 安装、ChatGPT 登录与图片权限、网络和 WebView2。普通界面无需配置 MCP；Agent 自动化另装原厂 Platform。

外层 ZIP 包含 Rhino 官方 Yak 包、离线 CPython 3.14.10 Windows embeddable、45 个离线依赖 wheel、安装/检查脚本和中文说明。ChatKit 固定 1.6.5 / FastAPI 0.162.0 / Uvicorn 0.54.0 / python-multipart 0.0.32，其他依赖也由下载 wheel 版本形成锁定清单。Python 安装到应用专用目录，不改变系统 Python/PATH；随机贴图 Worker 为 self-contained win-x64，无需另外安装 .NET Desktop Runtime。主插件仍由 Rhino 的 .NET 8 宿主运行。

主插件/UV Worker 从 B 已验证部署 `20261031-042010-c1715b5f387047098bf9bc54e2d12b3d` 精选复制，RHP SHA256 `00727C8D34E9D67FCAF278FE5ED3B8ED7A1A7078A3794194BBC330015F33071F`。不含开发 PDB、沙盒配置、模型、个人素材、Codex 二进制/登录/密钥或聊天记录。第三方许可证包含于 Yak、运行时 zip 或 wheel。未上传公共包服务器，也未代用户发送 ZIP。

## 构建

先准备 `artifacts/distribution-input` 中的官方 Python embeddable zip、requirements 对应的 Windows cp314 wheel（含 pip 26.2.1）及 self-contained TextureWorker publish 目录。使用 `scripts/Package-Windows.ps1 -DeploymentDirectory <已测试部署目录>` 创建带时间戳 ZIP，不更改正式 Rhino 注册。`distribution` 目录是安装脚本/说明源文件，使用 PowerShell 5.1 兼容的参数传递和字符串。

验证：从最终 ZIP 解压，在含中文/空格的空目录 `全新安装 Path 2` 用 `Install.ps1 -StageOnly -RuntimeDirectory <临时目录>` 验证离线首次安装与重复安装。成功导入 SDK、pip check 无冲突，使用该可搬移的嵌入 Python 运行真实 ChatKit SDK 协议夹具（污染 PYTHONHOME/PYTHONPATH，检查上传/SSE/持久化/token 轮换）。Python exe 数字签名 Valid。`Verify-WindowsPackage.py` 核对文件 SHA、Yak 依赖/许可证、RHP 与已测部署一致，在故意无效 DOTNET_ROOT 下实际运行随包独立贴图 Worker，验证图片和物理尺寸。

证据 `artifacts/distribution-validation/{verified,delivery}.json`、`install-final.log`、`delivery-install-check.log`、`reinstall.log`、`protocol.log`。首次安装器测试发现 Windows PowerShell 5.1 的 Python -c 内嵌双引号被移除，已改成正确引用并从 ZIP 重新验证。没有在本机运行正式 Yak 安装/写入正式 Rhino 注册，也没有在另一台干净 Windows 上进行实际 UI 验收；接收者依赖/账号/网络需按包内说明检查。

最终 ZIP SHA256：`F23F75E2D0C7F21E66ED44CDC75447ECF0E24307DF753F87A6A883A14054ABF9`。

参考：[Rhino Yak 包结构](https://developer.rhino3d.com/en/guides/yak/the-anatomy-of-a-package/)、[Yak 本地安装命令](https://developer.rhino3d.com/guides/yak/yak-cli-reference/)、[Python 3.14.10](https://www.python.org/downloads/release/python-31410/)、[Codex 安装登录](https://learn.chatgpt.com/docs/ide)。

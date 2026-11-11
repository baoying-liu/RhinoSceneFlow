# 沙盒 B：v0.2 自动化验收

## 2026-11-09 · 家里 B 完整更新到 0.22.4

本机 B ID `0d327c4c84f644f089b73834ffd93cfe`，管理 MCP 19540。通过已安装启动器的 `--start-mcp` 入口启动管理服务，再执行 build_test `87027f3741a5461489400878d15fb02b`；成功，0 warnings / 0 errors。部署目录 `20261110-041020-8ead82416d264ad281f62ff051d92687` 使用 UTC 命名，本地日期仍为 11 月 9 日。

最终 B Rhino PID116984，原厂 Platform22801，原生与 Web 均为 0.22.4。46 个部署 Web 文件（含 PhotoCraft）与同步源码逐字节一致，完整安装了最终前端修正；家里不依赖公司临时 Web 快照。原有两份画板文件哈希不变，B 文档为空、Modified=false。原厂 MCP 已打开 Web 工作台；独立 headless Edge 实际加载新图层面板，版本页脚正确、无页面错误。证据 `artifacts/rhino-B/home0224/{job,status,verified,browser-verified}.json` 和 `web-updated.png`。未使用系统鼠标、未调用生图、未制作新 ZIP、未更新正式 Rhino。

## 2026-10-31 v0.16.4 植物来源失败恢复

家里 B 最终任务 `1b61618c571442c699e5619e3d93c331` Succeeded，部署 `20261031-042010-c1715b5f387047098bf9bc54e2d12b3d`，PID 33868 / Platform 22801。用户的 Tamarindus indica 请求旧日志仅返回 Kew 与 USDA PDF：真实 Kew HTTP 403，PDF 不能作为 HTML 核实；可用 NParks 出现在搜索事件里却不在白名单。修复支持 NParks / IFAS / MBG 域名，并从实际搜索事件收集备选 URL、逐页读取核实，不采纳搜索摘要作为已核实证据。

插件实际经 `material_chat_start` 生成新透明 PNG 入库，资产 `6d51b311-bbd1-4e25-ac7f-cf2dba252745`，1333×1113，alpha 0..255，SHA 保持不变。中间测试发现正文提到另一植物可能误入来源，于最终版要求学名出现在标题/物种标题或明确 Scientific name 字段；实际 Dialium 页和 Tamarindus 属页被拒绝，新素材来源已按最终校验清理，保留 5 个已核实页面。`artifacts/botany0164/ready.json`、`final-identity-checks.json`、`image-verified.json`。植物库选中新素材，重开上轮已保存 Recovered 示例；不宣称恢复了未知退出时未保存的修改。

旧 PID 90640 在本轮接管时已经无法通过 B MCP 读取，随后记录 UnknownExit / code0，有 RhinoClosing/Monitor shutdown 阶段，无新 CrashEvents/Dumps；保留 failed close `7c24a4bdc82a4df7a37545961843aec0` 和审阅确认，不改写成成功关闭。本轮没有控制其他测试通道或正式 Rhino，也没有使用鼠标。中间 B 104676 由最终安装任务正常替换。

## 2026-10-30 家里 B v0.16.3 ChatKit

安装任务 `b4a04c30c50a4f47b705013d216c1f00` Succeeded，部署 `20261031-032736-19c7ae79b8db4f9e806d5b379a6cbd51`，当前 PID 90640 / Platform 22801。本机缺失 ChatKit venv，安装固定 requirements 后 pip check 通过；随后原生日志实际出现从 Rhino Python 3.9 标准库导入造成的 `SRE module mismatch`。v0.16.3 为 ChatKit 子进程加入 `-I -X utf8`，保留父进程环境。带故意污染 PYTHONHOME/PYTHONPATH 的 SDK 协议测试通过；原生 WebView SDK 最终 ready=true/error=null，`artifacts/rhino-B/home0161/chatkit-ready.json`，不是只检查后端进程。

系统提交内存约 96.3% 时启动被策略拒绝，未改变策略；正常关闭 B 释放内存后安装。PID 69292 NormalExit，70 对象的未保存工作由沙盒备份，恢复至原示例旁 `SceneFlow-Hillside-Retreat-Recovered-20261030-2327.3dm`，未覆盖原模型。恢复路径与备份在 `artifacts/home0161/chatkit-restored.json`；初次版本缺依赖和 Python 环境污染两次失败日志均保留。没有操作鼠标、正式 Rhino 或登录配置。

## 2026-10-30 家里 B v0.16.2 山地小屋

当前家里 B `0d327c4c84f644f089b73834ffd93cfe`，管理 19540 / Platform 22801。最终安装任务 `61fee537e4a54a21b54b6282098fadbd` Succeeded，部署 `20261031-030812-7138b04e107244678d527d06bbcb93af`，PID 69292。重开自有示例 `artifacts/examples/Hillside-Retreat/SceneFlow-Hillside-Retreat.3dm`，15 株（手工 4）、69 个有效 UV、五工具页健康、Modified=false。详见 [演示说明](HillsideDemo.md)。实际使用插件 AI 生成三种材质和一份透明植物；其他色板通过插件导入，不能称为 AI 生成。三个 Named Views，1200×900 PSD 四通道独立解码通过，最终导出 10736 ms。

完整最终检查 `artifacts/home0161/persistent-uv-final-build.log` 通过；映射数值等价/UV 修改/变换修改 oracle 在 `fingerprint-oracle.json`。首次重开暴露 32 个 Brep 箱式记录的归档哈希问题，语义指纹修复、正常重算、保存重开后通过，失败记录保留。PID 78340、24568 实际 NormalExit；原生 Open 引起 HTTP 10054 后重连核实相同 PID，未当作崩溃或绕过验证。没有使用鼠标或操作正式 Rhino。

## 2026-10-30 v0.16.1 植物缩略图界面

仅办公室 B，19540 管理 MCP / 22801 原厂 Platform。最终部署 `20261030-192503-3be88f99e1ad42eea68ece644f4094ca`，构建任务 `8a6b06af41b14dc1b3da5c1bcef5fe23`，真实正常关闭后重启任务 `d22c7b6e006042129499d36714619972` 成功。当前 PID **12568**，实例 `e5531381193148bd9a0ea659873c95e7`，B 窗口已显示。

原种植示例已重开，12 株／2 手工及 4 m 组合间距保留；植物库路径恢复到原库，当前为中文名称／两个区域的小方块模式。新增名称、布局切换与拖入测试见 Validation.md；最终实机图 `artifacts/rhino-B/plants0161/ready.png`，三素材图标／英文列表截图 `tiles-zh.png` / `list-en.png`。没有将合成测试素材加入原库。

标准检查与包 `artifacts/plant0161-release.log` 完成。PID 61576、13784 均 NormalExit/code0，无新 CrashEvents/Dumps；`exits.json`。旧 PID 65412 在管理器已关闭后只留下 closing 标记，缺退出码，按 UnknownExit 留档审阅，未改写为成功退出。未操作鼠标或正式 Rhino。

## 2026-10-30 v0.16 参数化种植对象

仅办公室 B `1cee488700ad42f59492743cc4a2a3fe`，管理 MCP 19540，原厂 Platform 22801。最终任务 `474db12c65c34839b0082156abfb8f4a` Succeeded；部署 **`20261030-180754-24f790b068db4aefbc229f6e77680cb8`**；当前实例 `fb02f615644d48babd6c86d1787e6f0c`，PID **65412**，窗口已显示。

标准检查／包见 `artifacts/plant016-release-final.log`。真实 B 验证单对象组合、多植物权重／间距、独立 Seed、连续点种、网格坡面／Brep 附着、源撤销／删除、拓扑不可靠时保留手工、复制／缩放、保存／New／Open 及五工具页。最终版本四个组合同时排队完成（含两倍缩放），临时副本已清理；`plants016/bounded-verified.json`。原生选中图统计橙色自动轮廓 4114 像素、青色手工轮廓 608 像素；`selection-colors.json`。详情与限制见 Validation.md / PlantGroups.md。

当前打开干净示例 `artifacts/examples/Planting-v016/SceneFlow-Planting-Composition-65412.3dm`，一个种植对象共 12 株，其中手工 2 株，承载面可修改。原共享库路径恢复，仅已有真实 Acer rubrum 的建议株距／依据由实际植物资料更新，未加入合成夹具。PNG、原生预览、选中轮廓、参数面板以及 individual/species/all 三份 PSD 均在同目录。`ready.json` 确认重开后的 12/2、五页健康、PSD 导出不改变 Modified。

标准 Rhino `_Save` 已在实际修改对象属性后成功覆盖当前示例，Modified=false；`native-save-verified.json`。之前 SDK WriteFile 同路径失败的记录仍保留，见 Validation.md。

输入 `RhinoSceneFlow` 打开工作区，选择种植对象自动打开参数；`RhinoSceneFlowPlant` 连续点种，Enter／Esc 结束。旧独立点兼容，不自动转换为组合。本轮未操作鼠标、未修改正式 Rhino 或其他通道。PID 15628、17672、45320、53240 均实际 NormalExit/code0、无新增 CrashEvents/Dumps，`exit-outcomes.json`。保留旧 PID 16092 UnknownExit 审阅记录，不改写历史结果。

## 2026-10-30 v0.15 植物

仅 B，管理 19540 / Platform 22801。实际生成、复用、整库整理、散布、三种 PSD、独立像素 oracle、ChatKit 消息和原生 New 取消通过，见 Validation.md / Planting.md。最终部署 `20261030-133859-afa56b19dafb49cd8fea7666a3bd0730`，任务 `14e2f38546a74e949a544b8d5fbef98e` 成功，PID 51448 / 实例 `c5cc32cac9bd4eeabf9b8f93335f620d`。最终 Alpha 轮廓几何预览实际透视／俯视检查及独立 PSD 解码通过，原生不再出现旧 PBR 卡片重叠矩形缺口。

10 月 29 日系统提交内存约 97.5% 超过 94% 上限，任务未准入，B 保存并正常关闭。10 月 30 日内存恢复约 48% 后重试同一 requestId 成功，未调整资源策略。`Open-PlantDelivery.py` 打开模型时一次 HTTP 10054，重连 PID 不变；`Finish-PlantDelivery.py` 五页 error=null、导出保持 Modified、1000×700 PSD 1966 / 721 ms。关闭任务 `02e40c26d0b04c28a731209f5748c6e4` 初次超时，实际窗口确认 Update Available；后续实例记录 NormalExit/code0、无新增 CrashEvents / Dumps，`native-cutout-exit.json`。超时证据保留，没有强制结束 Rhino 或安装更新。

示例 `artifacts/examples/Planting-v015/Planting-Demo-57912.3dm`、植物 PNG 及透视／俯视 PSD；唯一真实 Acer rubrum 已加入原库，合成夹具仍在独立测试库。`preview-0.png` / `preview-1.png` 已替换为最终原生预览；`native-cutout-verified.json` 是独立文件解码与保守内部覆盖核对，不是 Photoshop UI 验收。没有正式部署。

管理器重开后单独 `test` 因本会话未准备测试组合而被拒绝（任务 `811776ffd5c649418ee51fe915e2715e`，未启动 Rhino），随后按正常流程 `build_test` 成功：任务 `4a1b8686c8874390bd547699de774eae`，同一代码的新部署 `20261030-134551-01c7fbe15e5945e3917176be47cda4a9`。当前 B PID **16092** / Platform **22801**，实例 `3f259a3576b247ce90142989e1400145`。重开示例、四株植物恢复、原库路径、五工具页及文档未修改检查通过，`native-cutout-restart-ready.json` / `native-cutout-deployment.json`。B 后台保留供测试。

## 2026-10-29 v0.14 随机去重复

正常关闭后的最终重启任务 `74a3fca819e64d9ba7bd62361345ed63` 成功，当前测试实例 PID 31064，实例 `aa72097684e84150989c9ee1405421ce`，同一最终部署；五页健康与原库路径检查见 `restart-ready.json`。

最终 PID 68604 / Platform 22801，实例 `ca232f525f9146e39f399a9e97000edf`；420×950 侧栏与原生缓存球体通过。准备任务中原生 New 自动取消，重连后五页均健康；见 `new-verified.json`。关闭证据 `artifacts/random-final-close.json`。

仅 B。集成测试部署 `20261029-161926-8dc3f8f4288f4a30bab847a4fd71f5ea`，PID 62356 / Platform 22801，实例 `80137943bbbe40a491b5f1d15335fea7`：真实 AI 生成与默认建议、按物件变体、米制 UV、随机平铺、PSD 合并/分物件独立解码、取消和真实 Eto 草稿应用通过；原库已恢复。关闭 NormalExit/code0，无 crash events/new dumps。

最终 UI 换行与原生球体密度修订部署任务 `90110b98e9554367b42df4287f2d89a0`，部署 `20261029-162917-12b92e563e3d4015ab953a10bcf18ba8`。结果与最终 PID 见 `artifacts/rhino-B/random014/ready.json`。所有产物、原生截图、AI 状态及 PSD 解码在该目录；测试模型 `Random014-Demo-62356.3dm`。没有使用用户鼠标，没有更新正式 Rhino 注册。

## 最新 v0.13.3 共享本地材质库（2026-10-29）

部署 `20261029-144514-21ef13a3d30d44fba018469418b49c8e`，任务 `acc2d2c4abae47f5a6079b9be30f7669` 成功。B PID 58892 与两个外部进程共同写入私有库：自动刷新、草稿保留、过期属性 / 尺寸保存保护、跨文档共享与会话隔离通过。原库路径 `artifacts/rhino-B/workspace013/library` 已恢复，保留 4 个原材质。

PID 58892 **NormalExit**；重启任务 `8e1a75d35ecc4334b230319160cac24d` 成功。当前实例 `6641ca74df6f4ab0a79e3529bea523df`，PID **16780** / Platform **22801**，重开与原库恢复检查通过。证据 `artifacts/rhino-B/shared-library0133`，Core 多进程验证在标准 Build 中运行。没有操作正式 Rhino、其他通道或鼠标。

## 最新 v0.13.2 文档切换修复（2026-10-29）

当前部署 `20261029-141022-f253a7a8fd254d919d1cc07807628878`，安装任务 `0b206d577fdb487aaaeffccaa741cdbe` 成功。PID 63680 完成 10 次文档替换：AI 对话保持打开的 3 次 New / 3 次 Open、xatlas 计算中 New、ChatKit 未就绪时两次快速 New、PSD 卡片 / 细节页存在时 New。工具重建错误字段全部为空；Worker 取消且未跨文档回写；材质库应用与 UV 回归通过。

最终重启任务 `0f3605b61e6042c7aeec924e26abcd10` 成功，PID 63680 **NormalExit**。当前实例 `71f73e9881d14981b8f9ec22a7879e77`，PID **56356** / Platform **22801**，v0.13.2 重开检查通过。证据 `artifacts/rhino-B/document-switch`。未操作鼠标、未正式部署或操作其他通道。

原版 B PID 40352 的同路径异常 ExitCode 3、第一次修复未完成逻辑布局释放的失败证据仍保留；不把早期失败标为通过。根因与 Worker 范围见 [Document-Lifecycle.md](Document-Lifecycle.md)。

## 最新 v0.13.1 独立材质库（2026-10-29）

B 初次部署 `20261029-133625-c163b452062f46b398af3a574ca62956`，任务 `572c9b6f51a8454db5442efbaac32c11` 成功，实例 `ea9a95795db740fbb8c8f6f5d467e276`，PID 51908 / Platform 22801。独立库 / AI 页、同步选中材质和范围、从库按最新选择应用与自动 UV 已实测通过。命令 `RhinoSceneFlowMaterialLibrary`，MCP `material_workspace_open(page:library)`；五工具可独立停靠。

最终列表滚动修正版 `20261029-133829-e5608356616644c5b78c06fcbe99c25f` 已安装。任务 `ae2bce4dd4d94e068b188bc62192be63` 成功，PID 25448 的双向同步、A→B 实时应用、自动 UV 与列表布局复测通过，列表实测 230 DIP。重启任务 `5c913ff66244402e845cc03cf67d8c1f` 成功，PID 25448 NormalExit；当前实例 `2c979c77f0a44ba7b84952d664c1a1a7`，PID **25552** / Platform **22801**，重开后独立库及版本检查通过。证据 `artifacts/rhino-B/library0131/verified.json`、`library.png`、`ready.json`。

此前更新任务 `f0e6297285a3492ba7f8aae07be022ca` 的 CloseTimedOut 保留。用户取消 Rhino 自带更新提示后，旧 PID 51908 被管理器确认为 NormalExit；dump 证据见 Validation.md。未操作其他通道、未正式部署、未强制结束进程、未操作用户鼠标。

## 最新 v0.13 工作区（2026-10-28）

公司 B `1cee488700ad42f59492743cc4a2a3fe`，管理 MCP 19540；最终任务 `c75f0220677448cd9f8f9df98badbc96` Succeeded，部署 `20261028-213610-15e5ab02ec0e4bdc908e1bffc9ac57ba`，实例 `8378141635a1464eb07802da92e2f479`，PID **44696**，原厂 Platform **22801**。没有正式部署或改动其他通道。

输入 **RhinoSceneFlow** 打开四工具原生停靠工作区；旧材质、材质库与 PSD 命令仍可用。当前 B 为自有三物件 / 两个 Named Views 测试模型，最终保存 `artifacts/rhino-B/workspace013/SceneFlow-Workspace013-ready-abd18a35.3dm`；材质侧栏保留深蓝陶瓷选中和库预览，默认复用开启。B 测试库为 `artifacts/rhino-B/workspace013/library`，包含两种石材和本轮实际 AI 生成的陶瓷；早期 `library-v07` 原库保留。

实际 ChatKit 生成 / 检索、自动分类标签、整库整理、A→B 实时选择、窄 / 宽布局自动转换（宽 824）、模型重开、双预览 / 2K 预设 / 独立配置复制、两视图异步 PSD 及独立文件解码通过。样例 `artifacts/examples/Workspace013`。材质球用 Rhino 原生 RDK；没有鼠标操作，末尾只通过 computer-use 读取了一次原生保存文件锁状态。

本轮 PID 58024 的关闭异常与 dump 保留；修复宿主生命周期后 PID 49928 / 4344 两次正常关闭。对旧模型同路径保存曾触发原生只读文件锁提示，属于测试保存步骤；检查原生调用栈后改存新文件，没有覆盖被锁定文件。更多证据和限制见 Validation.md。

日期：2026-10-21。项目名称统一为 RhinoSceneFlow，原 RhinoPSD Git 历史保留。

## 环境与加载证据

- 沙盒管理 MCP：`http://127.0.0.1:19540`，绑定固定 B 通道 `1cee488700ad42f59492743cc4a2a3fe`。
- 实际测试 Rhino PID：`15500`；Rhino 内原厂 Platform MCP：`22801`。
- 插件：RhinoSceneFlow 0.2.0、Rhino-MCP-Platform 0.3.0、沙盒内置 Monitor。
- 准备版本：`20261021-173858-0cf7e33fe7464a54a231a711162f534b`。
- 实际加载成功任务：`bcd7ad3eb31a423a88cbfcf997b44489`。
- 只通过管理 MCP 操作 B；测试脚本先核对 Monitor PID 与管理器实例身份。没有修改 Codex 的 MCP 配置、启动其他 MCP 服务或推送正式插件。

## 导出验证

原厂 Platform `run_python` 调用 `RhinoSceneFlow.Plugin.McpApi.Execute(JSON)`；不使用鼠标、不弹出保存对话框。默认目录已设为本项目 `artifacts/exports`，每次生成唯一文件名。

| 视图 | 输出 | 颜色图层 | API 导出耗时 | 图层重合成最大预乘 RGBA 差异 |
| --- | --- | --- | --- | --- |
| 俯视 | 512 × 262 | 3 | 104 ms | 0.502/255 |
| 透视 | 512 × 262 | 3 | 103 ms | 1.486/255 |

这些耗时来自 4 个 Mesh 面对象、8 个三角形的简单场景，不代表大模型性能。

独立 psd-tools 1.26.0 解码真实文件，验证：

- 蓝色后景、红色前景、红色同色独立面、黄色锁定面，两个视图各 4 个 Rhino 投影位置的颜色与 alpha 均正确。
- 两个红色 Rhino 图层合并为一个 PSD 图层，名称含两个源图层名。
- 隐藏对象及隐藏父图层子对象不出现在 PSD。
- 红色遮挡位置的蓝色图层 alpha 为 0，背景透明。
- 图层重新合成与文件合成预览在量化容差内一致。
- 核心相机投影与 Rhino WorldToClient 的最大误差约 7.1e-14 像素（这组测试点）。
- 导出前后文档 Modified、对象数量、图层属性、相机、显示模式和选择状态一致。
- 错误版本、未知操作、不存在的文档、非法宽度、错误视图、已有文件保护均返回失败，不弹窗口。
- 原厂 `run_command` 调用 `_-RhinoSceneFlowExportPSD 128 _Enter`，无需路径输入，成功导出到默认目录（128 × 65、3 层）。

证据保留在忽略提交的 `artifacts/rhino-B/`：`smoke.json`、`verified.json`、示例 3DM、Rhino 视口捕获及 PSD 解码 PNG；PSD 在 `artifacts/exports/`。本报告可提交 Git，机器生成证据及用户连接凭据不提交。

## 边界与运行事件

本轮没有启动 Photoshop 应用，检查使用独立 PSD 解析库和像素验证。Brep、SubD、复杂块、大坐标、裁剪视图与大模型性能仍需要各自验收。

旧测试实例 PID 71540 曾被管理器记为 UnknownExit（退出码 0、无崩溃事件与 dump、无完整备份握手）。保留该失败结果，检查记录后通过管理接口确认退出，再显式启动新测试；没有把旧任务记为成功，也没有强制结束进程。新的 v0.2 加载和文件验收独立通过。

## v0.3.0 独立阴影增量验证

B 通道 PID 78996 的最终版本通过独立阴影验收：3,689 个原始 Brep/NURBS 参考采样、单色与透明边缘、墙面和曲面接收、背光面开关、Rhino Sun、样式参数、原生命令及默认 2048 像素输出。阴影样例 334,028 三角形，默认导出 1,736 ms。色层复杂形体回归仍通过。

修复了平滑曲面背光分界的三角碎纹；完整方法、失败证据与限制见 [Shadows.md](Shadows.md)。本次通过外部 psd-tools 解码及预览检查，未打开 Photoshop，未发布到正式 Rhino。

## 2026-10-22 准确性复核：已确认漏影

v0.3 的切平面法线偏移在接触反例中会越过遮挡片，导致应为 alpha=255 的阴影变成 0。旧版采样通过不构成完整准确性保证；太阳角度测试也补上了 BeginChange/EndChange 和实际角度断言。详情、对照及替代方案见 [Shadow-Alternatives.md](Shadow-Alternatives.md)。当前后端尚未修复该漏影，不应将研究验证完成解释为后端精度通过。

## 2026-10-22 v0.4 阴影体增量

固定 B 通道管理 MCP 19540 成功加载 v0.4.0，PID 26432、实际 Platform MCP 22801。任务 `16674f059d1745cabbb734352b91fd2d`，部署 `20261022-153951-18aa2cfcb65b41eda600206989d8e536`。由管理器备份关闭旧测试实例后加载新版；没有操作其他通道或正式 Rhino。

新命令 `RhinoSceneFlowExportShadowVolumePSD`、MCP `backend:"volume"`、默认 2048 输出和独立 PSD 解码通过；1,564 个原始曲面参考采样无不一致，已恢复已知近接漏影。1024 透视输出约 3.1 秒，2048 约 9.1 秒。Rhino Sun 自动/显式方向 PSD 字节一致，太阳及视图设置恢复。测试通过原厂 Platform 和文件检查完成，无鼠标、无 Photoshop 应用操作。

双曲面分界仍存在网格近似细碎纹理，旧射线后端仍有漏影。实际证据、比较方法和精度限制见 [Shadow-Volumes.md](Shadow-Volumes.md)；文件在 `artifacts/rhino-B/volumes/`。

## 2026-10-22 v0.4.1 准确性修正

最终通过固定 B 管理 MCP 19540 加载版本 0.4.1，PID 267632、实际 Platform 22801。任务 `1504b87713d84b95849de030552dd67d`，部署 `20261022-175142-f582f5b97d9f42858a55cc35678d3807`。没有操作其他通道，没有发布到正式 Rhino。

完整像素检查与回归在 PID 223868 完成：36,196 个包含明暗边界的解析子采样通过，双曲面碎影消失并保留真实阴影；原始 1,564 个稳定区采样及近接、样式、太阳、命令、默认输出通过。最终实例又导出字节相同的 1024 透视 PSD，证明最终构建保持已验收结果；相机、对象、选择及 Modified 状态不变。只使用原厂 MCP 与文件检查。

证据分开保留在 `artifacts/rhino-B/accuracy/` 和 `volumes-v041/`。最终透视文件为 `accuracy/final-perspective.psd`，修正前后放大图为 `accuracy/terminator-comparison.png`。默认 2048 输出约 34.1 秒。精度边界及失败迭代记录见 [Shadow-Accuracy.md](Shadow-Accuracy.md)。

## 2026-10-22 v0.5 Named View 导出面板

管理任务 `44278831ef4f4237b169e80e185e9fb7` 成功加载 B 的 PID 249608、Platform 22801，部署 `20261022-191804-c07133e5b33c442695602468510eb4e8`。只通过固定通道管理器构建及备份重启，没有发布到正式 Rhino。

真实 Eto 面板和命令、Named View 读取及尺寸刷新、Shaded/Rendered/Arctic 预览、三种画幅的批量输出、重名编号与覆盖策略、单通道和合并通道均通过。后台导出期间 UI 响应，实际取消按钮取消 2048 文件且无半成品残留。7 个 PSD 独立解码通过，主视图等状态保持。证据在 `artifacts/rhino-B/panel/`；详见 [Export-Panel.md](Export-Panel.md)。
## 2026-10-22 v0.5.1 预览窗口和完整太阳阴影

最终管理任务 `cfc26baefb804925acc38c1b2e771d1d` 成功，B 的 PID 68104、Platform 22801，部署 `20261022-202437-00aaf4fcb9034288b46cb739d9a0de39`。仅更新沙盒，未发布正式 Rhino。最终原生预览 Shaded/Rendered/Arctic、七个批量 PSD 独立解码通过；连续三次开关面板均只有原有四个文档视图、零浮动视图，状态保持，测试结束关闭面板。

阴影包含背光面与自身遮挡，无反射/GI/AO。当前模型完整 1024×587 阴影实测由 168.7 秒降至 15.9 秒，60 万像素 alpha 与旧完整计算一致。两个方向完整阴影 8,552 像素、双曲面边界 9,011 像素与独立几何参考一致；近接漏影、后台响应和真实取消按钮验证通过。后端验证 PID 153220 与最终构建的 Core DLL SHA256 相同。详细证据及范围见 [Shadow-Direct.md](Shadow-Direct.md)。

## 2026-10-23 v0.6 多卡片工作台

完整功能验证任务 `6ed3ff243dcd4231891f87ee650b9709`，B PID 265612、Platform 22801，部署 `20261023-164151-54953304d6494bca9916554477ca9ee5`。通过固定管理 MCP 19540 构建、加载与核对 PID；只在 B 使用原厂 Platform，不改服务配置，不操作用户鼠标。

同构建上完成多卡片设置、真实混合分层 PSD 与独立重合成；最终实例另完成临时 Named View 相机写回、两视图真实按钮后台导出、实际取消按钮及 8192×2048 材质输出。证据在 `artifacts/rhino-B/workbench/`：`verified.json`、`details-verified.json`、`async-verified.json`、`cancel-verified.json`、`8k-verified.json` 及布局 / 独立预览图。

早期三次无法归因的退出保留在管理器 UnknownExit 记录中，Successful=false；完整情况与一像素非接缝差异见 [Validation.md](Validation.md)。未发布正式 Rhino。使用命令仍为 `RhinoSceneFlowPanel`。

最终滚轮兼容修正后，任务 `06e652bddddf472295d4dcdc6e1f17c4` 加载 B PID 175732、Platform 22801，部署 `20261023-164847-a86ea98f993e4092919889ca750fb86f`。四张预览、合成滚轮事件、零浮动视图和小尺寸组合 PSD 复核通过；面板保留供查看，未自动创建额外视口。PID 265612 的管理器关闭请求握手缺失也按 UnknownExit 保留，不能当作正常退出。

## 2026-10-23 家用电脑 B

本机 B ID 为 `0d327c4c84f644f089b73834ffd93cfe`，管理 MCP 19540。本机重新构建 v0.6.0、修正 .NET 10 SDK 的数组 Reverse 解析冲突，通过沙盒加载并实测多卡片、PSD 图层 / 合成、真实异步与取消、8192×2048 材质输出。只修改 B；没有正式安装或发布。完整证据、输出路径及仍未确认原因的退出记录见 [家用电脑验证](Home-B-Validation.md)。

## 2026-10-26 公司电脑同步更新

源码已同步至 `c4e161b`，公司 B 保留的旧部署为 `20261023-164847-a86ea98f993e4092919889ca750fb86f`。本机 Build.ps1 零错误 / 警告且核心回归通过后，通过管理 MCP 19540 在固定公司 B 更新；没有修改 A 或正式 Rhino。

更新任务 `cead22d757c2482797b5c2eeb8443350` 成功，部署 `20261026-134519-79366444417f4ae9ba5bff01b89e1781`，PID 108352，原厂 Platform 实际端口 22801。4 张预览、合成滚轮事件、零浮动视图和 256×160 阴影 / 材质 PSD 输出验证通过；文档 / 视图状态保持。文件独立解码及重合成最大预乘 RGBA 误差约 1.773/255。证据：`artifacts/rhino-B/office-update-20261026.json`。

管理服务起初关闭，电脑控制接口报 native pipe unavailable；通过安装版自带 `--start-mcp` 参数开启服务后完成操作，没有模拟鼠标输入。测试实例及工作台保留供用户测试；历史退出问题未在本次短时更新检查中重新验收。
# 2026-10-26 v0.7 材质库 B 部署

仅办公室 B `1cee488700ad42f59492743cc4a2a3fe`，管理服务 19540。最终任务 `cce650d2025042a682a587340470158b` Succeeded，部署 `20261026-161231-d736d19c7e454145afe95ee34781e070`，实例 `aa211c7d7eb2457fb74610000111e896`，Rhino PID 116016，原厂 Platform 22801。未修改正式 Rhino、其他通道或 Platform 私有实现。

材质库命令 `RhinoSceneFlowMaterials`；B 测试库 `artifacts/materials/library-v07`。自有示例模型 `artifacts/rhino-B/materials/demo/SceneFlow-Materials-Demo.3dm` 包含石材平面、棋盘格箱体 / 圆柱和两个 Named Views，材质面板可直接试用。`Prepare-MaterialDemo.py` 只接受空文档或完全属于该 demo 的文档。

构建、真实 SDK / Eto / Undo 以及独立 PSD 解析记录见 [Validation.md](Validation.md)。v0.7 测试期间未观察到新的异常退出；保留此前 v0.6 UnknownExit 证据，不认定旧问题已修复。
# 2026-10-26 v0.8 B 实机验收

办公室 B，19540 管理服务、22801 原厂 Platform。最终任务 `b500a553d5f64083b5353de89eafc2cb` Succeeded，部署 `20261026-210109-7bc0cdfa2e96465482ea80502974a8b9`，实例 `e473368138dd4f6690243a9c6159b2ea`，PID 26764。

`RhinoSceneFlowWorldUV`：独立米制 UV。`RhinoSceneFlowMaterials`：先选对象，打开简洁生成 / 应用窗口。`RhinoSceneFlowMaterialLibrary`：原完整材质编辑器。示例仍是 `artifacts/rhino-B/materials/demo/SceneFlow-Materials-Demo.3dm`，库仍为 `artifacts/materials/library-v07`（名称沿用，不代表当前插件版本）。

验收覆盖有效 UV 复用、失效补算、图层混合对象进度、真实 Eto 阶段刷新 / 参考图片 / 回填 / 取消及原生 Undo。详见 Validation.md。中间部署因 Rhino 隐藏更新询问而关闭超时，选择不安装后正常退出再重试；未强制结束进程，未改其他通道。
# 2026-10-27 v0.9 B 更新

仅办公室 B `1cee488700ad42f59492743cc4a2a3fe`，19540 管理端、22801 原厂 Platform。最终构建任务 `18c79b8b12a04b568a5a8c96f5374fca` 成功，部署 `20261027-184155-039d831265654c26a3e66ba84c83977b`，实例 `ebc9d2917aff4beb8a71b5934b2dbca9`，PID 60896。

`RhinoSceneFlowMaterials` 现在自动调用本机已登录的 Codex 生成图片，并跟随当前 Rhino 选择。实测参考图 → 新 PNG → 自动入库 / 选中、失败 / 重试 / 取消、重开面板继续显示任务、A/B 切换及图层范围均通过。旧手动 Agent API 保留，按钮不再只提交等待任务。无额外 MCP 服务、无独立 API key。详见 Validation.md / Materials.md。

示例模型仍在 `artifacts/rhino-B/materials/demo/SceneFlow-Materials-Demo.3dm`，材质库仍为 `artifacts/materials/library-v07`。本轮旧退出记录与失败任务保留，未把 UnknownExit 记为测试通过。


## 最新 v0.11（2026-10-27）

办公室 B，管理 MCP 19540，原厂 Platform 22801。最终成功任务 `9e9c822a08f94c7580b151c647d3bbba`；部署 `20261027-221139-9a8160dde1a04d5d8307f2195e6d4db6`；实例 `d0f4cd958d9c4e909360e13dff6c334f`；PID **78296**。仅更新测试沙盒，未发布正式 Rhino。

ChatKit 实际对话、上传参考图、真实新图片、入库 / 选中和重开历史均通过。xatlas 92,928 面组合约 26.112 秒，原几何未变，3dm 映射 / hash 持久化、取消及过期输入拒绝通过。材质库仍为 `artifacts/materials/library-v07`。测试模型 `artifacts/rhino-B/xatlas/Xatlas_0b67f78e.3dm`；完整样例在 `artifacts/examples/ChatKit-Xatlas`。详情与限制见 Validation.md 和 ChatKit-Xatlas.md。

通过管理器显示了 B 窗口以初始化原生 GPU 视图；没有使用鼠标。当前 B 模型 / 面板保留供手工尝试。旧失败、未知退出和主动取消记录保留，不视为成功。


## 最新 v0.12（2026-10-28）

任务 `66d93f90374a428da0df53aafd58251b`，部署 `20261028-151756-6ecc52b29a834dfc84d2c06fc3de60ed`，实例 `47abcdb63065428687fc43d77752e42e`，PID 66776 / Platform 22801。已修复原生 UV 回投影与渲染朝向，新增沿中心线管体展开；实测及限制见 UV-Continuity.md / Validation.md。示例模型 `artifacts/rhino-B/uv-v012/UV-Continuity-Brick.3dm`，预览 / PSD 在 `artifacts/examples/UV-v012`。已实际重开并检查恢复后的原生网格；没有使用鼠标或修改正式 Rhino。
## 2026-10-30 家里 B 更新 v0.16.1

家里 B `0d327c4c84f644f089b73834ffd93cfe`，管理 19540，原厂 Platform 22801。安装任务 `0c2b6bc79b4b48d18374e3f961f4a249` Succeeded，部署 `20261031-024925-bb7eb5098d66449fa73acb329a2cee99`，PID 78340。MCP 实测版本 0.16.1，五工具页 error=null，最后打开种植页，文档 Modified=false。家里使用 VS 18，原生 UV 构建脚本改为匹配本机 VS 17/18；完整 Build.ps1 验证及打包通过。证据 `artifacts/home0161/build.log`、`artifacts/rhino-B/home0161/ready.json`。窗口由沙盒显示；没有操作鼠标或正式 Rhino。本次未重新生成植物，也未重新运行公司示例的全部交互回归。

## 2026-11-02 office B update to v0.16.4

Source 022c61f matched origin/master after fetch. Previous office deployment was 20261030-192503-3be88f99e1ad42eea68ece644f4094ca. Build.ps1 completed all core validation and packaging; sandbox build_test job 1f0607a149f843d4b87abf44e2c0fc54 succeeded with zero build warnings/errors. Deployment: 20261102-145406-3f8defee7d7e4893a8ddba2a390bb773; PID 59900, original Platform port 22801. Public describe returned 0.16.4; all five workspace tools opened with error=null. Dedicated ChatKit runtime imports passed under -I -X utf8. No image generation, full UI browser acceptance or PSD export was repeated in this update check. Only fixed office B was updated; no formal Rhino or other channel changes, no mouse use. Evidence: artifacts/office-20261102-build.log, artifacts/office-20261102-status.json and artifacts/rhino-B/office-20261102-ready.json. Instance remains hidden under the existing silent-test setting.

## 2026-11-02 v0.17 Plants List and selection properties

Only office B 1cee488700ad42f59492743cc4a2a3fe was updated through management MCP 19540. Final build_test job bd3dc33d89f643a89d935a10723cef11 succeeded (zero warnings/errors); deployment 20261102-171012-a2e2c1383ee542ccb10861d53d93fd98, PID 59052, Platform 22801, RHP SHA256 64D3FBB2BE411A7868766BF73A328F3E361902EE9FC5ABC30B7D0FEC4DE6FB3F. Public describe returned 0.17.0. Build.ps1 full validation/package completed: artifacts/v017-build-accepted.log. No formal Rhino, other channel, user material library content or mouse input was changed. The managed B window was shown for WPF Loaded/layout inspection, not through simulated input.

Verified: genuine Eto selection/deselection events and native viewport selection in both directions; rename/layer/hidden/locked attributes; hidden/locked group enumeration and lock restoration after hide/show; same-material edits, object isolation and repeat reuse, layer isolation; custom plant type/position/scale/mirror, unchanged density count, exclusion of original automatic instance, persistence across all seeds and carrier deformation, real 3dm Save/Open; custom reset and legacy loose-plant compatibility. Actual properties controls prepared valid world UV before applying PBR changes. Rhino native _Undo/_Redo round-trip passed using ContentUndoHelper (undo.json). New/Open kept PID 59052 and rebuilt all seven tools with error=null; final document is empty, Modified=false, original library preference restored. B remains visible with the properties tool open.

PSD individual/species/all exports at 320x240 succeeded and were independently decoded with psd-tools: 36/6/5 pixel layers respectively, plants above shadow and layer-color passes. Species/all independent composite maximum channel difference was 2/255 (group quantization); not Photoshop UI acceptance. These are synthetic alpha regression plants in an isolated library, not newly AI-generated botanical imagery. Evidence: artifacts/rhino-B/properties017/{setup,selection,verified,psd-verified,undo,ui,reset,ready,workspace-final}.json; PSD-*; plantsList.png and properties.png are WPF layout captures and exclude the native viewport.

Preserved intermediate build errors, failed script assertions, source logs and HTTP resets. Initial direct RhinoDoc.Undo/Redo probes left an active scripted undo/redo record; the isolated fixture finishes its prior scripted record and tests actual native commands after Platform returns. Initial custom snapshot implementation was replaced with Rhino's documented ContentUndoHelper. Open/New HTTP resets alone were not treated as crashes or passes; reconnected PID/document/tool checks supplied the evidence. Raw pointer mouse double-click gestures and interactive GetPoint movement were implemented but not simulated; single-plant API edits and alpha-pick math share the same stored group data. No promise of single-plant Gumball support in this version.

## 2026-11-02 office Hillside reproduction

Rebuilt the home Hillside example through the existing SceneFlow workflow on office B only: PID 59052, plugin 0.17.0, Platform 22801. Real new Betula nigra PNG and three textures generated/classified through the plugin; 69 geometry objects received calibrated UV/materials; 15 trees in group 73fb8208-d869-4935-bb7e-23a6e81e4641 include four manual plants. Actual 1200x900 PSD export: 11 pixel layers, 11039 ms, independent psd-tools decoding confirmed Arctic/material/Shadow/plants. Native Save/Open validation retained the PID, all 69 UV records valid, 15/4 plants, three Named Views, all seven tool errors null and Modified=false. Model is %LOCALAPPDATA%/RhinoSceneFlow/Demos/HillsideRetreat/SceneFlow-Hillside-Retreat-Office.3dm. Original OneDrive-path saves failed and were preserved; local-path native overwrite/reopen passed, root cause unconfirmed. No formal Rhino or mouse input. See docs/HillsideDemo.md and artifacts/examples/Hillside-Retreat/office-reopened.json for complete paths, asset IDs and evidence.

## 2026-11-02 v0.17.1 isolated plant editing

Office B only (management MCP 19540, original Platform 22801). Final build_test job 9a9f6d0b5c514d0a8f08ab1d3285ac09 succeeded, deployment 20261102-183026-a1e4552329744b6ea0175569c53ba445, PID 24484. Build.ps1 full validation/package passed with zero warnings/errors (artifacts/plant-edit0171-accepted-build.log). No formal Rhino, other channel, mouse input or shared library content changes.

Actual Eto GridView CellDoubleClick entered isolation. All 70 normal document objects (including the group root) became unselectable; single-member move kept the other 14 rows identical, copy raised the count from 15 to 16 with no new Rhino object, and cancel restored exact parameter JSON, rows and modes. Real conduit PickGumball found translate and scale handles, ScaleMode XYZ. The actual registered SDK OnMouseDoubleClick override selected an alpha-visible plant and enabled its handle after Platform completion. Native _Undo/_Redo during isolation and _Undo after exit restored exact parameters without stranded locks. Saving during editing finished the session; native Open retained all saved member poses; native New while editing cleared session/Gumball state and kept the PID and tool health. Evidence: artifacts/rhino-B/plant-edit0171/{isolation,callbacks,gumball,undo,saved,reopened,new,ready}.json. No OS pointer gestures or interactive GetTransform.Get drag were simulated; tests exercise native event handlers, native handle picking and the shared transform commit path.

Retained failed evidence: PID 69264 StackOverflowException dump and plant-edit0171-crash-stack.log identify record-generated Vec3.PrintMembers -> Unit -> ToString recursion from SyncHandle. Explicit scalar formatting fixes both the handle stamp and Vec3 diagnostics (zero-vector regression included). Locked-root derived Replace initially failed; the native GeometryBase/ignoreModes overload now updates it without unlocking. Native attribute Undo alone failed after derived mesh replacement; PlantParameterUndo snapshots and end-of-replay restoration passed the final native regression. Earlier Platform undo-scope and handle-timer harness failures remain separate files. The manager correctly refused relaunch until the crash evidence was reviewed/acknowledged; failed jobs remain failed.

Before testing, the dirty user model was copied to %LOCALAPPDATA%/RhinoSceneFlow/Demos/HillsideRetreat/Backups/Before-PlantEdit-20261102-125921.3dm. Final ready model is SceneFlow-Hillside-Retreat-PlantEdit-Fixed.3dm in that HillsideRetreat directory: original 15-tree layout restored, all Named View export settings copied, Modified=false. Original Office.3dm and backup are preserved. A separate PlantEdit-Regression.3dm contains the persistence test edit.

## 2026-11-02 v0.17.2 interaction corrections

Office B only, management MCP 19540 / original Platform 22801. Final build_test 570a8b1c9f9c41048ebdcfe41227230d succeeded: deployment 20261102-185111-c5b0df2825b543abb60c4c8d5a52d021, PID 15672, describe 0.17.2. Initial full Build.ps1 passed (plant-edit0172-full-build.log); later targeted plugin builds and final sandbox build passed with zero warnings/errors. Final package plugin/core/deps were copied from that exact tested deployment. No formal Rhino, library assets or OS mouse input changes.

Root causes: transient empty Eto selection could exit isolation; the native Gumball hover gate could reject plant double-clicks; GetFrustumLine was traversed far-to-near, making ground behind visible trees act like foreground blockers; picking alpha .15 disagreed with native preview .02; preview-only depth separation was missing from picking. Blank double-click had no exit path. Final code scopes picking to the active group, orients rays using CameraDirection, follows wireframe/Xray and per-object mode overrides, matches display alpha/depth, restores semantic list selection and finishes on a no-plant double-click. Context uses temporary pipeline locked-color settings plus gray materials for other plant groups; no document/layer/material colors or persistent display modes are changed.

Test-PlantEditInteraction: 12 actual Eto list double-click / asynchronous empty-selection cycles remain isolated; all 15 plants pass registered native OnMouseDown handlers; a .126-alpha leaf is pickable; native blank double-click exits, viewport double-click re-enters and blank exits again. Original group JSON unchanged, lock markers removed, Modified=false. Test-PlantEditGrey: native rendered before/isolated/after captures; 151498 saturated pixels become neutral and before/after maximum RGB difference is exactly 0. Pipeline locked settings restored exactly. Test-PlantPickOcclusion: a locked owned plane in front blocks the plant, its wireframe object override restores the hit, and a wireframe viewport permits the hit; the owned plane is removed in finally. Existing isolation regression confirms one-member move/copy/cancel and unchanged other rows/object count. Native New from active gray isolation retained PID and rebuilt the two open tools without errors. Raw physical double-click/drag gestures were not injected; actual SDK callbacks and native rendering supplied the evidence.

Retained two failed interaction reports: initial ray test only found six plants; a wire-mode guard alone did not fix the rendered scene. The size-only CaptureToBitmap overload produced wireframe-looking images even though the viewport mode was SceneFlow Demo - Rendered; explicit DisplayAttributes captures corrected that test inference. The actual decisive evidence was ray origin below the scene and direction towards the camera, then 15/15 hits after orienting it. These were assertion failures, not Rhino crashes.

Evidence: artifacts/rhino-B/plant-edit0172/{interaction,grey,grey-pixels,occlusion,isolation,new,ready}.json and rendered-{before,isolated,after}.png. Original model was backed up to Backups/Before-PlantEdit-20261102-134412.3dm before restarting. Final B reopened the original SceneFlow-Hillside-Retreat-PlantEdit-Fixed.3dm, exact group parameters restored, no lock markers, Modified=false, both open tool errors null. No model changes from regression were saved over it.

## 2026-11-02 v0.17.3 single-plant motion

Office B only: final build_test 2fbe72da9c534d81b043e31d84e59137, deployment 20261102-193752-1d4afc708e574409b1676eb0e8fc4c26, PID 39120, original Platform 22801. Targeted build and full Build.ps1 validation/package passed with zero warnings/errors (plant-edit0173-build.log, plant-edit0173-full-build.log). No formal Rhino, library writes or OS pointer input.

The previous GetTransform had an empty OnDynamicDraw while changing a PostDrawObjects billboard, leaving old static feedback and no proper dynamic plant renderer. New begin/end hooks redraw static background once; only the moving member is excluded, its cached mesh/LOD is pinned and its own OnDynamicDraw draws one transformed card. Ctrl-copy retains the original. Rhino foreground feedback is temporary and can draw over context while dragging; committed frames restore ordinary depth/occlusion. FullFrameRedrawDuringGet remains false to avoid regenerating the whole scene on each mouse move. The dynamic renderer owns no document edits and releases the pinned reference on cancel/exit/New.

Valid frozen layouts now commit edited rows/proxy/work stamp immediately, without the .35-second timer, .45-second debounce, carrier meshing/welding or scatter. Carrier/settings/unit key mismatch retains the existing async layout path. Existing custom parameter Undo remains in use. Baseline on the same 15-tree user model: old API submission 7.2867 ms but usable layout 1299.3983 ms, initially busy. New 12 sequential updates: median 11.9777 ms, maximum 46.9569 ms, busy=false and Gumball available immediately each time; other rows unchanged. Single-member copy also immediately ready. These timings describe pose commit availability, not end-to-end pointer latency or GPU FPS.

Test-PlantMotionPreview uses the exact shared DrawDrag renderer through a native DrawForeground harness, the same renderer called by GetPoint.OnDynamicDraw, without injecting pointer gestures or blocking Get. Native frames: 11101 pixels at the old tree rectangle disappear from static background; moving in either direction leaves exactly zero changed pixels there compared with that clean background. New positions draw 7191 / 6930 changed pixels. End/cancel and copy-source retention differ by at most 1/255 at a handful of pixels (mean below .000002); the initial exact-zero restoration assertion was retained as preview-pixels-first.json, then bounded for this observed GPU rounding. Dynamic draw submission measured 2.4302 / 1.7285 ms, not a frame-rate measurement. See commit.json, preview.json and preview-pixels.json in artifacts/rhino-B/plant-edit0173.

Native Undo/Redo, immediate pose Save/Open with identical rows, and New from an active pinned preview all passed with the same PID. Final reopen confirms pinned=null, no active editing/dragging and original user rows/parameters preserved. Physical pointer drag feel still requires the user test; source callbacks, dynamic renderer, pixel output and pose commit path were verified independently.

Before testing the user model was dirty. It was preserved in Backups/Before-PlantEdit-20261102-143500.3dm. Final ready file is %LOCALAPPDATA%/RhinoSceneFlow/Demos/HillsideRetreat/SceneFlow-Hillside-Retreat-PlantMotion-Fixed.3dm, a new copy including those unsaved user edits, with Named View export settings copied. It was natively reopened, 15 trees, Modified=false, no pinned preview. Original PlantEdit-Fixed.3dm was not overwritten. Evidence: baseline/commit/preview/preview-pixels/undo/saved/reopened/new/ready.json and motion-*.png. B is shown with Plants List/properties ready.

## 2026-11-02 v0.17.4 selection-outline shadow fix

Reproduced the reported detached gray tree contour in a full native capture on B PID 39120, with no active drag and no pinned preview. A/B captures on the dirty user model proved the contour depends on both outlines and shadows: its sky ROI contained 2118 pixels below 245; shadows-off, outlines-cleared and plants-suppressed each removed that contour. The scene had no extra tree object. It was not merely a stale mouse feedback buffer.

Move ordinary selection lines from PostDrawObjects into DrawForeground; keep only physical plant meshes in PostDrawObjects. A shared DrawOutline helper enables depth testing and disables depth writing with balanced push/pop/finally for normal and dynamic feedback. This keeps proper UI colors/occlusion while preventing the contour from entering shadow/depth effects. Do not disable legitimate plant/scene shadows as a workaround. Native pipeline stage reference: https://developer.rhino3d.com/api/rhinocommon/type/rhino.display.displaypipeline/ .

Final office B build_test 7b51fb182f8648cdaa5e7e58371d20a8 succeeded: deployment 20261102-200100-038c641b89c043168831e562327e9faf, PID 26944, Platform 22801, plugin 0.17.4. Targeted build plus full Build.ps1 validation/package passed, zero warnings/errors (plant-outline0174-build.log / plant-outline0174-full-build.log). No formal Rhino, shared library writes or OS pointer input.

Test-PlantOutlineShadow native rendered captures: phantom ROI dark-pixel count is now 0 with outlines ON; comparing outlines ON/OFF produces exactly 0 changed pixels outside projected plant rectangles (maximum RGB difference 0). The shadows-on/off control still changes 278493 scene pixels. Green/cyan/orange UI pixels remain 3482/3205/5696. Thus the fix preserves both highlight cues and legitimate scene shadows. Evidence: artifacts/rhino-B/plant-outline0174/{ab-pixels,outline,verified}.json and fixed-{outlined,no-outline,no-shadows}.png. Old full capture and shadow-off/no-outline/no-plants controls retained.

Motion regression passed: 12 immediate moves median 12.1584 ms, maximum 49.4602 ms, ready with Gumball/no pending layout, unchanged other members; copy immediate. Shared dynamic renderer pixel oracle: old position unchanged versus clean background for both directions, copy retains its source exactly and cancel restoration differs by at most 1/255. This is native callback/render testing, not physical pointer gesture or FPS measurement.

Before restart, dirty user changes were saved to Backups/Before-PlantEdit-20261102-145953.3dm. Final model is %LOCALAPPDATA%/RhinoSceneFlow/Demos/HillsideRetreat/SceneFlow-Hillside-Retreat-PlantOutline-Fixed.3dm, preserving those changes and copied Named View export settings. Native reopen verified identical parameters/15 poses, no pinned preview, Modified=false. Resumed the user original isolated group/member (custom:77231c114bf74c93af4dc0d8ee896487) after saving, so temporary locks are not saved to the 3dm. Original PlantMotion-Fixed.3dm remains untouched; ready.json records the final state.

## 2026-11-03 · v0.18.0 AI 后期 Web 工作台（第一阶段）

新增第八个原生 Tool / 命令 RhinoSceneFlowPostProduction；前七个面板 GUID 和顺序保留。独立 Bearer/Host/Origin 校验的 loopback HTTP UI，不新增 MCP。通过原厂 Platform 的 postproduction_start/status 提交文件快照及 UI 线程捕获的当前文档元数据。独立串行解析进程、持久项目/对话/配置；New/Open、面板关闭和 Rhino 退出不结束 Web 服务。

完整 Build.ps1 两次通过，最终日志 artifacts/postproduction-final-build.log，零编译警告/错误，已有 Core/原生 UV/植物/PSD/跨进程库验证通过。开发包已包含 PostProduction 静态资源；离线 ZIP 未生成，旧离线 wheels 缺 PSD 依赖，打包器新增缺失依赖拒绝保护。

真实 HTTP/PSD/文本模型验证 scripts/Test-PostProduction.py：1200×900 Hillside PSD、13 个图层/组、1024 最大块/128 每侧上下文产生 4 个无重叠核心，完整覆盖画布；两种导入、源 SHA256、401/403、配置陈旧 409、媒体白名单、JSON 下载、服务重启后项目/配置/对话保持。最终独立证据 artifacts/postproduction/518a4e198daf4985bb6677974acc48c4/verified.json。--chat 实际使用本机 Codex ChatGPT 登录和演示预览，返回真实描述；没有生图。第一轮测试脚本误将结果 text 字段断言为 reply，修正测试后完整重跑通过，保留原目录。

浏览器原生页面验证分组用途联动、分块 1024→512 后 4→20、保存状态、原始合成预览和真实聊天排队/运行状态；使用浏览器 DOM 接口，不输入系统鼠标。首次选取 size 的 label locator 未匹配，重新观察后以页面实际 #size 控件验证，不当作产品失败。

B 首次部署 20261103-184348-05d3f08d32dc4e26b9321cf6d3d96e4a / PID 45272，公共 MCP 交接、面板和原生 New 通过，文件/对象/Modified 保持。最终部署 20261103-184736-f8fa24cff64147899feeff2c3dc6f4c5；加载任务 eb3fe6fbdda44b8695eed59ef6e381b5 Succeeded，PID 9396，Platform 22801。所有五个 Web 源文件与部署文件 SHA 一致。最终交接项目 1cb1ebf8f64649c2b7fcfac2ac29cfdb，Web PID 41456；原生 Open 已保存的 PlantOutline-Fixed 演示，70 个对象、Modified=false，post 工具重绑且 error=null，服务/PSD 项目仍可访问。证据 artifacts/rhino-B/postproduction018/{handoff,open,new}.json；带 bearer 的 launch-private.json 只在忽略目录，不打印/提交。

最终更新任务 cd907bd77a4e47069383bb690df383f4 曾因旧 PID 45272 CloseTimedOut 失败，备份完成、端口释放但进程未退；失败证据原样保留。通过只读窗口检查实际确认 Update Available（Yes/No）阻塞退出，键盘 Alt+N 拒绝更新后进程退出，未使用系统鼠标、强杀或安装 Rhino 更新。后续 Return 的窗口已消失错误不当作额外操作成功；经理记录仍保留原 CloseTimedOut，未冒称有 NormalExit/code0。确认旧进程不存在后显式提交 test，实际加载最终版本。Native New/Open 的 HTTP 10054 经同 PID/文档/面板重查确认，不当作崩溃。

边界：当前只完成 PSD 导入/原始合成预览、图层用途、GPT 描述、分块规划和 JSON 项目；NetVips/OpenCV、实际分块生图、结构漂移检测、拼接融合、结果 PSD 尚未接入。psd-tools 对复杂 Photoshop 效果有合成限制；第一版限制 8-bit RGB、8192 边长、256 层/组、512 块和 2GB，独立进程不等于系统内存配额隔离。详见 docs/PostProduction.md。

## 2026-11-03 · v0.19.0 实际 AI 后期与 PNG 输出

完整 Build.ps1 通过，零警告/错误（artifacts/postproduction019-full-build.log）。实际生图使用既有 Codex 登录的独立 image-only 执行器，文本描述助手仍禁用工具；没有固定承诺某个图像模型型号。psd-tools、libvips Python 绑定与 OpenCV 已接入；不生成结果 PSD。本次没有制作新版离线 ZIP。

真实 Hillside 测试完成单块→整图复用：共 3 次图像调用（共享风格 1 次、图块 2 次），最终 1200×900 PNG。89,955 个保护像素、821,952 个只读像素及原始 alpha 均通过逐字节核对；258,044 个像素改变。PNG SHA256 a77538cb5a46745e2fd26207bfcb7fc33d608787e7bfc4c7a10360aceeb3e420。原生浏览器下载文件哈希相同。原始生成尺寸与回填尺寸分别报告。边界诊断仅供人工复核，不构成几何不漂移保证。证据 artifacts/postproduction-images/6037710ff7834f34b12138d30b79a723/verified-final.json；示例 artifacts/examples/PostProduction-v019。

保留原两项目的 project.json/source.psd，SHA 完全一致，另建示例项目 d54dfb287159466394f9e4e15799c447。固定夹具融合、来源路径/线程/时间验证、并发原子 JSON、取消/恢复、导入权限与重启持久化均通过。Windows 临时 rename/read sharing 故障已通过唯一临时名和有界重试修复；实际已接受图块恢复时未重生，保留首次失败证据。

Office B channel 1cee488700ad42f59492743cc4a2a3fe，加载任务 3430613e9d464405a7a289ae225e091a Succeeded；deployment 20261103-220417-79c5f26c51b74052891e5a27c8705280，PID 31060，原厂 Platform 22801，插件 0.19.0。原厂 MCP postproduction_request 的 GET 与 POST 实测通过，POST 恢复/融合结果同哈希、无额外生图。Native New/Open 后同 PID，已恢复 PlantOutline-Fixed.3dm，70 个对象、Modified=false，工具 error=null。证据 artifacts/rhino-B/postproduction019/{bridge-verified,bridge-post-verified,ready}.json。未操作正式 Rhino，未使用系统鼠标。

旧 PID 9396 的升级任务 6db231b5a7a5497d86b7b36ac2e7c2e6 曾 CloseTimedOut；备份已完成、端口释放，用户确认选择 No/暂不更新后，确认旧进程退出再加载。保留原超时记录，不冒称 NormalExit/code0。最终独立 Web PID 66816、端口 58945 保持运行，示例比较页面已打开；原有项目与模型不覆盖。


## 2026-11-04 · 家里 B 更新至 v0.19.0

家里 B 0d327c4c84f644f089b73834ffd93cfe，仅通过管理 MCP 19540 构建/加载；任务 153dd948369b4976b28c8c20c4a55105 Succeeded，部署 20261105-041952-9385324b092944bfbb22f579dd97d12f（UTC 名称），PID 147608，原厂 Platform 22801。编译零警告/错误，原生 describe 确认 0.19.0，八个工具全部实例化且 error=null，ChatKit ready。初次测试页名 plants 无效被 API 正常拒绝，改为实际 plantsList 后通过，没有改动产品。

原默认 Python 3.14 venv 缺少新版图像依赖；保留为 %LOCALAPPDATA%/RhinoSceneFlow/chatkit-runtime-before019-20261104，默认路径创建独立 CPython 3.11 venv 并安装两个固定 requirements，pip check 通过。ChatKit SDK 协议（fixture agent，不调用模型）、raster 保护/alpha/排除/融合 pixel oracle、fresh image 来源与 Windows 原子 JSON 竞争检查通过。证据 artifacts/postproduction-raster/73a0e23925ff4f51af98e12979a50ff6/verified.json、artifacts/postproduction-provenance/83ca4d2853e94f69859632b0a77c8382/verified.json。

原厂 MCP postproduction_request /api/status 实测服务 0.19.0、codexAvailable/generationAvailable=true，Web PID 59236；本机 Codex ChatGPT 登录有效。这一轮未消耗生图额度，不把接口能力检查称为新的真实生图测试。当前本机空文档上 Native New/Open 空白夹具/New 通过，同一 PID、八工具重绑健康；10054 后按文档与 PID 重连确认，不当作崩溃。最终空白未命名文档 Modified=false，B 窗口显示且 AI 素材页打开。证据 artifacts/rhino-B/home019/{native-ready,new,open,ready}.json，postproduction019/bridge-verified.json，提交/运行环境日志 artifacts/home019。没有使用系统鼠标、没有部署正式 Rhino、没有修改原材质/植物库、没有制作离线 ZIP。


## 2026-11-07 · v0.19.1 对比线拖动

对比模式新增可聚焦的 DOM slider 中线，Pointer Capture 支持左右拖动、画布外夹紧、取消/丢失捕获释放；箭头 1%、Shift+箭头 10%、Home/End，保留顶部 range。按画布实际矩形而非整个黑色视口计算位置，ResizeObserver 跟随布局尺寸。非对比模式/无结果时隐藏并禁用；不触发分块点击。结果摘要显示复用、无可修改像素、待确认数量。本次没有修改生图提示词/蒙版/融合算法，也没有加入“变化强度”参数。

node scripts/Test-PostProductionCompare.cjs 通过：双向移动/捕获/范围夹紧、键盘、留白和缩放位置、选择不变、无结果隐藏。此为事件/几何测试 harness，不是浏览器实际手势。CUA 本机浏览器 host 和 native pipe 均不可用，未绕过工具做 UI 自动化，未使用系统鼠标。浏览器实际拖拽视觉验收仍待用户操作。

家里 B 管理任务 56d5136797a64b2cbb01fd3870ce7e10 Succeeded，部署 20261107-191419-0f6483f5b5bd4cbd97464a42d8690d94，PID 105960，原厂 Platform 22801。构建零警告/错误，原生 describe 与 postproduction_request /api/status 确认 0.19.1，文档对象/Modified 不变；服务 HTML/JS/CSS 与修改源码逐字节相同。测试前 B 未运行，无替换/关闭用户文档。证据 artifacts/compare0191/interaction-verified.json 与 artifacts/rhino-B/compare0191/verified.json。未消耗生图额度，不宣称新的图像质量测试。


## 2026-11-07 · v0.20.0 Studio 双视图与两阶段渲染

新首页为本机 React/Konva/perfect-freehand Studio，旧页面保留 /legacy。稳定图片 ID、独立画布 pose/frame、列表与画布双向定位、右侧参数/标注/历史、缩略图与离屏裁剪、小地图、手绘压感点/箭头/文字/Label、修改/保护区域、最多四参考图的编号参考板。提交冻结输入；源 PSD 仅在源节点提供图层用途和硬像素保护，生成子节点不贴回原粗模型像素。whole 使用现有实际 image-only runner，detail 直接复用已确认整图，不再生成额外风格图。任务检查/接受/重试、整图中断恢复、描述助手（真实文本、禁工具）、自动保存和工程包、三格式导出、中英文设置及原厂 MCP JSON save/export 均接入。实现/边界见 Studio.md。

完整 Build.ps1 两次通过，零编译警告/错误，Core/UV/植物/PSD/跨进程库检查保持通过；artifacts/boards020-{full,final}-build.log。新 HTTP/文件/worker 验证最终 artifacts/boards020/b3788163214147a2b165f6f8ac857957/verified.json：布局与身份分离、409、防无效 overlap、分层 PSD 像素锁定/结构用途区别、精确 alpha/只读像素、四参考合板、工程包往返与路径穿越拒绝、PNG/JPEG/WebP、JSON 保存导出和语言。queued/waiting cancellation 与冻结快照见 board-invariants/4a2318a226864092bccc2a1df1f483e5/verified.json；测试明确阻塞图像队列，不消费模型。旧 raster/provenance 回归见 postproduction-raster/16168a3cc76c4383b459b92108d5af10 与 postproduction-provenance/8188d3000db64fc2bd489d76669129c6。

真实图像测试目录 artifacts/boards020/d5517c8376e8414db53492f648345fe6：一次整图、三次高清尝试，共四个图片执行请求及四份新 PNG 线程/哈希收据（不当作账户计费统计），另一次真实描述回复。源为明确标注的二维粗略体块夹具，不冒称在 Rhino 建立三维模型。整图补充木饰面、窗框与屋面细节。第一高清输入空白过大导致放大，保留失败；改为实际上下文紧凑补边。初次 Canny 边缘也被错误当作硬保护条带，出现重影，已分离诊断边缘与 alpha 硬保护。最终候选仍触发 P90 人工复核，独立查看后显式接受并合并至 1024×768；不是几何一致性证明。中间 Windows 长临时文件名超过路径限制的融合失败，通过不重复目标 basename 的 UUID 临时文件修复；恢复仅重融合，无额外图片请求。原失败证据和中间输出保留，示例不使用旧重影结果。

前端 web/postproduction/test-dom.cjs 通过，零控制台错误：列表/画布、双向定位、位置不变、小地图、直接中线 pointer/keyboard 事件、语言与预设持久化。此为 jsdom + 模拟 raster context 的组件测试，非真实浏览器视觉/手写屏测试。CUA browser host/native pipe 均不可用，未绕过工具发送鼠标或用其他 GUI 自动化。实际笔压设备、拖拽手感和视觉布局仍需用户实测。

仅家里 B 0d327c4c84f644f089b73834ffd93cfe，管理 19540 / 原厂 Platform 22801。最终任务 21985b95984e44ca9b1b3372ff6d5073 Succeeded，部署 20261107-202624-27ed07c75a214794b4f6b9bc30695272，PID 9940。16 个 Web 资源与源码逐字节一致。八原生工具 error=null；原厂 MCP GET boards / POST save / POST export 通过，PNG 与样例哈希一致，无文件对话框。之前 PID 94604 原生 New/Open/恢复空文档通过，HTTP10054 按同 PID/文档重查；最终部署 RHP 哈希与其一致。最终 PID 9940 八页健康、0 对象、Modified=false。105960、111664、94604 的 exit.json 均 NormalExit/code0；未强杀 Rhino。旧 0.19.1 Web 无项目/活动作业，正常 shutdown 后启动新服务。

持久 Web PID 112316 / port 14602 / version 0.20.0，API 和资源核对通过。测试示例以新画板 13b1c78c8c134e85ace7f2d02dec5a02 导入，三图分别是粗略二维示意、实际 AI 整图和检查后高清；初始界面中文，可在设置切换。工程包和图片 artifacts/examples/Studio-v020。没有覆盖原库/模型或更新正式 Rhino，没有制作新离线 ZIP。原生和发布证据 artifacts/rhino-B/boards020、artifacts/boards020-B；旧 PID94604 的原始验收保留在 verified-pid94604。临时 QA 服务已正常停止，生产 Web 和 B 保持运行。


## 2026-11-07 · v0.21.0 可追溯节点工作流

列表树/折叠和画布连线共享稳定 parentId；原文件后缀保留。创建子级/同级只建立待生成白板，空描述/标注/参考，继承所选配置（原图用默认）。原始输入只读，更新写回同一节点，新结果成功后锁定；撤销回到 baseline。输入快照固定版本，父图更新只使直接子级变紫；草稿黄，两种状态同时保留。生图期间内容禁止编辑，布局不影响生成状态。归档为有效祖先遍历加 AI 意图说明，可逆；不自动恢复像素。默认2备份/+3独立扩容/成功后自动清理/手动删除/配置签出及只读预览导出；引用字节不物理删除。读旧板时稳定迁移，保存时落盘。输入检查可定位原始来源链。描述助手原先使用 reply、实际返回 text 的字段不一致在真实归档测试中暴露，已统一并成功复测。首次失败日志保留。

Build.ps1 全验证通过，零警告/错误，artifacts/workflow021-build.log；后续最终管理构建也零警告/错误。HTTP/PSD/像素/四参考板/包往返/格式/权限回归 artifacts/boards020/b8e16093e83144da8c67cf2a062ddd6c。状态/备份/归档/取消/包测试 artifacts/workflow021/3ef8dce3952b4c3fb84cbdb6735d92fd；queued/waiting cancellation artifacts/board-invariants/81313476bf8e40f79052caee3f5fbce0。组件测试 artifacts/workflow021-http/0ef0d14ed33f4ccab41e313bd18f4576/dom-verified.json：反复选图、列表/画布、锁定、草稿自动保存/撤销、同级白板、树折叠，零 console errors。该测试使用 jsdom/模拟 canvas，不是实际浏览器视觉和设备手势验收；黑屏修复针对选择加载顺序、预览重挂载及画布自动定位，仍需用户视觉复测。

独立合成建筑夹具实际请求1次 image-only 生成，来源新图收据 newImage=true，267379像素改变；没有修改用户案例。artifacts/boards020/8b4b2f66bb054139af29591e05254527/verified.json。归档执行两次实际禁工具文本任务，第一次模型已返回文本但字段不匹配失败；修复后 archive-verified.json 证明 AI摘要、后代变紫、解除归档均通过，未再调用图片模型。

仅家里 B 0d327c4c84f644f089b73834ffd93cfe，管理19540/原厂Platform22801。最终任务669d8889963446e3a687d80537c06881 Succeeded；deployment 20261107-220123-eda2bc0f718f44c9a9f41e7c7a41d88f，PID121792，describe=0.21.0，8工具error=null。真实 New/Open/New 后同PID，原生空白未命名文档0对象/Modified=false，10054按新文档重连检查，不认定崩溃。Web PID21864/port4962/version0.21.0；16资源与最终源码逐字节匹配。原山地案例9916447c152344a3a7b654d6eefa133a仍2节点，asset/preview/尺寸均与更新前备份一致；已打开列表原图。证据 artifacts/rhino-B/workflow021；更新前完整画板资产在 artifacts/workflow021-before-update。未改正式Rhino、未用鼠标、未创建新离线ZIP；临时测试服务已正常shutdown。


## 2026-11-07 · 待生成白板重影修复

用户截图复现的原因：Compare 对所有带父级的节点默认启用 compare，白板也画了父级底图；pendingBoard 又放了 opacity .25 的嵌套 img，而原 CSS 仅约束 .comparison>img，嵌套图保持固有大小、居中后与底图错位。源预览 hash 与 input.preview 相同，输入文件没有重影。修复为 pending 只画一张正常比例输入图，明确 absolute/inset/100%/object-fit；禁用结果对比和混合、移除中央文字遮挡，画布白板也不再淡化输入。pending→completed 后才恢复对比。

web/postproduction/test-workflow-dom.cjs 扩展并通过：唯一 img、无底图/结果 canvas/对比线、CSS 填框、相同节点白板转结果及原有列表/锁定/保存回归，零 console errors。证据 artifacts/workflow021-http/efedb9e45359401d89af53d88331759b/dom-verified.json；这是 jsdom 组件/CSS 断言，不是浏览器实际截图。未消费生图额度。

管理 MCP B build 1c0f7b93e830406ca89a16eff8803129 Succeeded，零警告/错误，新 payload 20261107-222310-f5b590228a41417bae98bbb29c47240c。仅把已核对的 JS/CSS/许可证静态文件热更新到当前 B 原生 .rhp 所在目录；原文件已备份 artifacts/preview021-before。Rhino PID121792、Web PID21864 均未重启；实际 HTTP 返回与源文件逐字节相同，案例 board JSON 前后一致。证据 artifacts/rhino-B/workflow021/preview-hotfix-verified.json。刷新页面即可载入，正式 Rhino 未改动。


## 2026-11-07 · v0.22.0 理解框布局、历史与鼠标交互

主体按理解框占位，分层子树布局、新建整齐放置、移动与调整frame避让、附件跟随。前后端同算法；拖动暂态布局/端口实时跟随，松开才提交。每条子分支−/+端口在理解框边缘；画布/列表独立折叠，折叠整理。单击不缩放，显式定位。删除为级联软删除；持久Undo/Redo原子存于board.json，Ctrl+Z/Ctrl+R，版本发布为历史边界，源像素不覆写。右键捕获平移/取消/原地菜单，滚轮预览滚动与可选上一张下一张设置。

完整 Build.ps1 通过，零警告/错误：artifacts/layout022-build.log。HTTP/worker/PSD/保护像素/包/导出回归 artifacts/boards020/4052183d9ab14e3f932283f51212850e；取消/冻结输入 board-invariants/d6f60ae4f21742ffa4eac78aaf3869f4。布局/持久历史/删除/框避让/新建单步undo：artifacts/layout022/b09470a9515242449727ee803cae1363/{verified,js-verified}.json，80节点Python/JS精确一致、12次拖动样本无框重叠。组件事件 artifacts/workflow021-http/fbb5dc4d1fec4d33bcb6e09522ddbfbf/layout-dom-verified.json：真实Konva fire驱动拖动/Transform，松开前连线更新、仅松开落盘、无变换放大反馈、独立折叠、CtrlZ/CtrlR删除/框调整、右键只改相机/菜单保留、滚轮设置等，零console错误。这是jsdom/模拟canvas，不是浏览器视觉/手写设备验收；本轮0模型请求。

B 19540管理任务9c38e006f8ce432188d36ccd9afde2ed成功，部署20261107-224457-7be1ee6a18c24e10a91d41b260a7e3c5，PID113512。追加右键/滚轮后管理build 9447d61f025744cbae92ebbeb48967f5成功，最终源payload 20261107-224754-9dac3b6dd7094cbca6174af64e529493；RHP哈希与活动实例相同，启动Web前同步17资源到当前B payload。原厂Platform22801确认describe0.22、八工具error=null；原生New/Open/New同PID、0对象/Modified=false，10054按新文档重连验证。Web113816/9320/version0.22；实际HTTP JS/CSS与源码一致。

原山地案例6节点，通过原厂MCP实际执行arrange→undo→redo，框无重叠，所有像素/预览/配置/标注/父级/输入/版本/来源不变。已在画布概览打开；只调整布局和相机。更新前完整画板在artifacts/layout022-before；验收与MCP往返在artifacts/rhino-B/layout022/verified.json及bridge-*.json。旧0.21 Web正常shutdown；临时组件服务已关闭。未使用系统鼠标，未改正式Rhino，未生成新离线ZIP。


## 2026-11-07 · 列表默认翻图与“平滑”连续浏览

根据用户澄清，默认滚轮切换上一张/下一张，预览工具栏增加“平滑”开关。开启时沿列表当前顺序把图片纵向排列成连续页面；原生滚动，不以固定间隔强制切图。图片按宽高比占位，IntersectionObserver仅加载可见区域及400px预取，预览使用单层像素Canvas，无父图叠加。滚动不更换编辑对象；点击卡片选中，从侧栏选择则定位卡片；“单图对比”关闭平滑并进入所选图的对比。参考/白板仍显示各自身份，备份查看保持单独预览。设置与工具栏共享持久选项。旧scroll含义为滚动单张图，增加listWheelVersion=2一次迁移到默认navigate，此后保留用户选择。

test-smooth-dom.cjs通过：默认前后翻图、开关/持久化、纵向卡片顺序、单层预览、滚动不改编辑目标、卡片选中不跳动、侧栏定位、返回对比、像素/参数/来源不变；零console错误。证据 artifacts/workflow021-http/03b410221db64121a1dfd42e41a95862/smooth-verified.json。更新后的完整画布/历史/右键事件回归 artifacts/workflow021-http/ce4bdbd2b84140f4bd063847742ef50a/layout-dom-verified.json也通过。以上为jsdom/模拟绘图，不是浏览器视觉验收。0模型请求。

管理B build aa11dad7437c42ee9de72e3b9a1ad3bb成功，零警告/错误，payload20261107-230948-8731f08e115249eab9e11fd5c25a8ea5。确认RHP与活动B哈希一致后仅同步Web模块/资源，不重启Rhino113512；旧服务shutdown初次立即Ensure复用了退出中的旧服务，保留连接拒绝证据，重试启动后确认新Web115892/7446、版本0.22、listWheelVersion2/default navigate、HTTP JS/CSS与源码一致。山地案例节点数据前后一致，只切为列表原图供试用。验收 artifacts/rhino-B/smooth022/verified.json。临时服务关闭；正式Rhino不变，没有ZIP。


## 2026-11-07 · 白板显示、侧栏定位与折叠样式修正

待生成结果改为白色：单图和平滑卡片是左白/右固定输入，通用WipeHandle拖动/键盘控制裁切；画布不加载/绘制源CanvasImage，缩略图同样白色，输入检查仍显示真实输入。所有底层资产、模型输入和参数不变。侧栏新增默认开启autoLocate，控制侧栏对画布/连续列表的定位；画布普通点击仍不缩放。隐藏祖先通过layout reveal展开，仅修改画布折叠状态。

找到实际折叠UI失效原因：通用.resource>button把按钮设为opacity0/absolute/right-bottom，树按钮与定位按钮重叠。新增.resource>.treeToggle明确static/opacity1、叶子占位，测试真实CSS级联，不仅测试点击函数。移除搜索时忽略collapsed的逻辑。

组件/样式/Konva regression artifacts/workflow021-http/0783e285418749d28829b72088e2d1a8/blank-focus-verified.json：左右裁切/拖动、纯白Rect与0个Image、白缩略图、自动定位开关/展开隐藏路径、画布点击不缩放、可见static折叠按钮真正隐藏子项、画布/列表独立、平滑白板对比、输入不变；零console错误。旧工作流组件测试更新为新规范并通过，证据workflow021-http/6b1d413ded3640d6ac06689f83f1a04a/dom-verified.json。布局/前后端80节点parity回归layout022/7c6b59322989474ea47089dfbc15a346通过。以上是jsdom/模拟绘图，非实际浏览器视觉验收；0模型调用。

B管理build 1b9b266bfa9d4d99b330b15739c38293成功，零警告/错误；payload20261107-231943-c3752f26704e4de4a98fa1ab651c9d4c。与活动B的RHP哈希一致，仅同步Web并等待旧服务退出后重启Web，Rhino113512未重启，8工具健康/0对象/Modified=false。Web120528/8647，实际HTTP JS/CSS与源一致，autoLocate默认true。案例6节点数据前后完全一致，仅切换列表并选中已有白板0f5fe4b8b51648018795353119d5652d展示。artifacts/rhino-B/blank022/{before,verified,browser}.json保留证据。无正式Rhino修改，无ZIP，临时服务已关闭。


## 2026-11-07 · 切图淡入与平滑模式结果对比

根因：Compare按node/backup key反复挂载，available先重置900×600再由ResizeObserver测实际尺寸；draftNotice和工具栏换行也改变可用高度。修复为按board挂载、测量初值0且保留，固定工具栏40px、白板提示改行内。decodedPreview原子等待结果/父级输入解码，旧帧保留到新帧就绪；过期请求忽略。仅opacity140ms过渡，旧帧独立尺寸居中，170ms释放；Canvas在layout effect绘制。新旧图不同宽高比各自fit，不对旧图套新比例。快速切换不回放迟到图片。

平滑FeedImage此前仅pending渲染wipe，已生成图片且blend100时连父图都未加载。现在有input的可见卡片均加载固定输入，左结果/右输入互补裁切，共用WipeHandle；pending仍左白，根图不伪造父图。保持懒加载、卡片选择及参数不变。

test-preview-transition-dom.cjs最终证据 workflow021-http/80ff6f5bcba44e2f854646a806174fcc/preview-transition-verified.json：1400×900 viewport只测量一次，延迟加载期间旧图尺寸保持、迟到结果忽略、140ms淡入/旧帧清理、已生成卡片wipe拖动与裁切、源根无伪造对比、节点数据不变。白板/定位/折叠回归 workflow021-http/87ee5ea459004ddb97ab5eae36bef9e5/blank-focus-verified.json；流程组件 workflow021-http/67e3acb43b764042aeccb68e2a6ccfe9/dom-verified.json通过，均零console错误。均为jsdom/模拟canvas，不是浏览器动画视觉验收。没有调用模型。

B管理build4f2939b8663547d0a1e8f120d8ab6a11成功，零警告/错误；payload20261107-233341-ef6042389c6a4a64a578f67dc4bd6f2a。只原子热更新活动B的JS/CSS/许可文件，旧资源已备份；Rhino113512与Web120528/8647均不重启。实际HTTP资源与源码匹配，案例JSON前后一致。证据 artifacts/rhino-B/fade022/verified.json。刷新现有页面载入，不需重生成图片。正式Rhino未改，0图像/文本模型请求，无ZIP。

## 2026-11-07 · 输入模板与恢复默认 Web 更新

管理构建 `6e8357548d804852ae044b9d129e48db` 成功，产物 `20261107-235132-b750ccf3d1f0414dbff57490b64751ac`。确认原生 RHP 哈希相同，仅复制 PostProduction 到 B 当前加载目录 `20261107-224457-7be1ee6a18c24e10a91d41b260a7e3c5`，同时同步 artifacts/package。Rhino PID 113512 保持运行、8 tools 健康、未修改空文档。优雅停止旧 Web PID120528，再由原厂 MCP 启动 Web PID117712 / port3961；真实案例已选中原图并用列表打开。安装／数据保留证据 `artifacts/rhino-B/defaults022`。无新 ZIP、无模型调用。

## 2026-11-07 · 画布工具更新

管理构建 `aedc6c1484cd4eed8af92a5d1563b52b` 成功，产物 `20261108-011229-4dce45c541bc489a82ac56d67ed2f24e`（目录时间为 UTC）。验证 RHP 哈希一致，仅将 board.js／board.css 及依赖声明同步到当前 B `20261107-224457-7be1ee6a18c24e10a91d41b260a7e3c5` 和 artifacts/package。Rhino 与 Web 保持运行，未重启、未改用户画板。原厂 MCP 打开新版页面并核对完成；真实 Edge 测试及安装证据 `artifacts/rhino-B/tools022`。最初对不公开的 LICENSE 路由核对返回404，随后改为文件核对；JS/CSS路由精确匹配。

## 2026-11-07 · 标注编辑与笔刷控制

管理构建 `921ebe89bd824d139c95b9b9017477a2`，新产物目录 `20261108-033150-bf752dd4ed7d4219829d7cc9dd84dba3`（UTC目录时间）。RHP 哈希不变，仅将 board.js／board.css 和依赖声明同步到 B 当前目录 `20261107-224457-7be1ee6a18c24e10a91d41b260a7e3c5` 与 artifacts/package。Rhino PID113512 及 Web 保持运行，无需重启。真实画板全部字段保留，原厂 MCP 打开页面并确认完成；原生／静态资源／真实浏览器证据 `artifacts/rhino-B/annotation022`。未生成新图片、未改真实案例标注。

## 2026-11-07 · 文字原位编辑静态更新

管理构建 `1ea197453a9a41938aa5453ac1ff8957` 成功，产物 `20261108-035105-89a7574b9ccd4a93925619c5026c14e7`（UTC目录时间）。原生 RHP 哈希相同，仅同步 board.js／board.css／依赖声明到 B 当前 `20261107-224457-7be1ee6a18c24e10a91d41b260a7e3c5` 及 artifacts/package。Rhino PID113512、Web 保持运行，无需重启。真实画板全字段未变，原厂 MCP 打开新版并核对完成；真实 B headless Edge 加载无错误，证据 `artifacts/rhino-B/inline022`。

## 2026-11-07 · 空间考虑框与参考资源更新

构建 `5ab97fca3c634bb9a5516560600692f4` 成功，产物 `20261108-041523-946172951f084b7bab58b224d56e32e6`（UTC目录时间）。原生 RHP 哈希相同，将完整 PostProduction（含新 canvas_context.py）同步到 B 当前 `20261107-224457-7be1ee6a18c24e10a91d41b260a7e3c5` 和 artifacts/package。确认无活动任务后，经 /api/shutdown 优雅退出 Web PID87704，等待停止后通过原厂 MCP 启动 Web PID86356；Rhino PID113512 保持运行。真实画板只迁移 marks 默认值和引用固定归属／错误 stale 标记，ID、位置、像素、其余图节点配置及版本不变。原厂 MCP 打开并核对新版完成；安装／数据比较／浏览器／context API 证据 `artifacts/rhino-B/spatial022`。未制作新 ZIP、未调用图像模型。

## 2026-11-07 · 标注删除入口统一

构建 `9738fc7868e242f09a44fac5c6bce428` 成功，产物 `20261108-042441-f2124550f63c4a0c9dd0a9f4bc433424`（UTC）。RHP 哈希相同，仅同步 board.js／board.css／依赖声明到 B 当前 `20261107-224457-7be1ee6a18c24e10a91d41b260a7e3c5` 及 artifacts/package。无须重启 Rhino/Web；真实画板逐字段未变，原厂 MCP 打开并核对新版完成，见 `artifacts/rhino-B/delete022`。

## 2026-11-07 · 边界与参考图框更新

初次构建 `75261a3b9c83495e9cf231af9b123d97`，产物 `20261108-044233-72455490e3be4a2b8c9adb1e3f3d07b1`。原生哈希一致，确认无活动任务，优雅停止旧 Web 后同步完整 PostProduction，原厂 MCP 启动 Web PID103296，Rhino PID113512 保持运行。最终列表入口构建 `e67ff4a007074dab978c7faa25d426e2` / `20261108-044522-06f280f37cbe49ca97b888632be7a2aa` 仅同步静态资源，不再重启 Web。B 当前原生目录仍为 `20261107-224457-7be1ee6a18c24e10a91d41b260a7e3c5`，artifacts/package 同步。真实画板完全保留，页面已通过原厂 MCP 打开并检查完成，证据 `artifacts/rhino-B/gallery022`。未生成新 ZIP／未调用图像模型。


## 2026-11-08 · PhotoCraft 编辑参考层

最终构建 `5abd54a2d16f4a9585c6ccf94faeca18`，发布目录 `20261108-053457-59f282c2971d46b2ba9bf5eed5303e47`；0 warnings / 0 errors。原生 RHP SHA256 仍为 `f63dc235dc6958519c9b9294c22c0d3f615829df8c441067907c301bd7179bcb`，B Rhino PID113512 不重启，活动原生目录仍为 `20261107-224457-7be1ee6a18c24e10a91d41b260a7e3c5`。

确认无 queued/running/review 任务后优雅停止 Web，复制最终完整 PostProduction（43 文件，含 PhotoCraft 15 个原始文件、许可与来源清单），原厂 Platform 启动最终 Web PID6160 / port14620。活动目录、构建产物、源码、artifacts/package 的资源哈希一致；不新增 MCP 服务，不更新 ZIP。首次旧端口的浏览器检查遇到启动竞态，等待新 PID 就绪后重新检查通过。

真实案例 `9916447c152344a3a7b654d6eefa133a` 保持 8 个节点（含删除节点），新编辑器实际载入山地小屋图并取消返回，画板逐字段不变。最终 `browser-verified.json` / `live-B-editor.png` / `live-B-returned.png` / `installed.json` 在 `artifacts/rhino-B/photocraft022`。不使用用户系统鼠标，不调用图像模型。临时测试服务会在完成后优雅关闭，B 服务保留。

原厂 MCP 已打开最终工作台，`browser-launch.json` 确认为 completed；打开后真实画板仍逐字段一致。最终资源核验见 `photocraft022/verified.json`。


## 2026-11-08 · 编辑参考层小眼睛

构建 `0a16f7477666468f8076f5d6af22d041` / `20261108-172310-76366dc6abdf43f4b0034d83dffb99db`，0 warnings / 0 errors。原生 RHP 未变、Rhino PID113512 不重启。无活动图像任务后优雅重启 Web，最终 PID123364 / port6086；复制完整 PostProduction 到 B 原生活动目录及 artifacts/package，原生活动目录仍是 `20261107-224457-7be1ee6a18c24e10a91d41b260a7e3c5`。

当前真实案例 8 节点、原始图已有 1 份用户编辑参考层。真实 Edge 已加载默认可见的叠加层，叠加层不参与 hit testing；不修改选择／视图／参考层设置，整个画板逐字段未变。证据 `artifacts/rhino-B/reference-visibility022/browser-verified.json` 和 `live-B-visible-reference.png`。测试画笔/隐藏切换在隔离工程完成，不使用用户鼠标、不调用 AI 生图、不打新 ZIP。


## 2026-11-09 ? ?? B ?? 0.22.0

?? B ID `1cee488700ad42f59492743cc4a2a3fe`????????????????? Rhino??????? `dc8913c865ad44cca3d7c565ba13e935` build_test ???0 warnings / 0 errors??? `20261109-145303-032a7958776847c1889aa8dbed68c68c`????? RhinoSceneFlow 0.22.0?Rhino PID115716?Platform 22801?Web PID97904 / port51937?Codex ????? MCP describe ? postproduction_start/status ??????AI ????????43 ????????PhotoCraft 15 ????? SHA ????????????? Modified=false??????? Rhino???? AI?

?????????????????? Platform 0.3.0 ?????? 0.4.0????????? Yak ? net48/net8 ? Acp.dll ??????????? net8.0 ?????? net48 ???? DLL ???????????????????????????????EnvironmentPluginVerification ????? `%LOCALAPPDATA%/RhinoDevSandbox/experiments/environment-plugins-79b8db873e894ca7b63f6485138af7af`??? DLL ??????????????MCP 19540 ???

Windows ??/??? PhotoCraft 13 ???????? CRLF????? SHA/SRI???? LF ???????? SHA ????????????????? `.gitattributes` ? vendor `-text` ??????????? `artifacts/company022` ? `artifacts/rhino-B/company022/verified.json`?????????? ZIP?

## 2026-11-09 · 0.22.1 任务流程与原生工具栏

公司 B 的最终构建/加载任务 ec3c0458cf5347c6a1c986f6dad896ac 成功，PID 99296，原厂 Platform 22801。部署 20261109-191637-51ce0454f1ee4a8088b7c102a3b65fdf，describe 与 Web 均为 0.22.1，Web PID 112892。原生 RhinoSceneFlowToolbar 命令实际打开 SceneFlow 容器，RhinoSceneFlow.rui 的九个宏全部解析到已注册命令；位于 LOCALAPPDATA/RhinoSceneFlow/Toolbars/Sandbox，正式安装使用独立 User 路径。原生 Settings/Toolbars 可选 RhinoSceneFlow/SceneFlow。未改正式 Rhino，B 文档为空、Modified=false。

原始两份本机工程在正常关闭旧 Web / 启动新版后 board.json SHA 保持不变。随后仅在自有 Hillside 审计工程切换列表/画布、检查输入，没有新增 AI 图片或改源像素。新版页面已通过原厂 MCP 打开；管理 MCP 显示 B 窗口，不发送系统鼠标事件。

输入前检经原厂 postproduction_request POST /api/boards/.../nodes/.../preflight 实测通过：1200×900，938636 可改 / 1080000 总像素，空描述无标注时 ready=false，未触发生图。直接 HTTP/真实 headless Edge 也验证了实际案例首屏描述、mask、画布和已有像素/版本不变。16 个活动代码/静态/RUI 文件与源码逐字节一致，公共 board.js/css 一致；构建包静态资源同步。证据 artifacts/rhino-B/taskflow0221/{native,verified,bridge}.json 与 artifacts/ui-audit-20261109/{task-label-state,release-case-verified}.json。

测试阶段保留了前几次构建/部署记录。先前 115716 的 UnknownExit 已在工具栏审计中审核并保留，未改称通过；本节最终成功任务独立记录。没有制作新离线 ZIP，没有实际 AI 生图/高清画质测试。完整操作说明见 Task-Workflow-0221.md。

## 2026-11-10 · 家里 B · 0.22.5 Rhino → Web 审计

最终管理任务 904cfa8ee45948df8cea7f7e1d9df19c 成功，PID 50132，原厂 Platform 22801，部署 20261111-042652-96a23b44e0ff456fbdc908e011c3decf。describe、Web 及实际中文页脚均为 0.22.5，46 个 PostProduction 文件与源码逐字节相同。八个原生工具 error=null；独立 Hillside 副本已打开，原模型保留。

修复旧任务配置恢复后锁定保存冲突、AI 分组开关恢复与 pending 状态、参考区域删除后误收起、输入编辑时整板 Ctrl+R、窄侧栏 PSD 尺寸布局及页脚版本来源。生成前检查新增实际输出尺寸。真实无界面 Edge 最终十条交互流程通过；普通与特殊层 PhotoCraft 真实编辑 roundtrip 通过。

实际链路：600×450 PSD（材质贴图、阴影、植物、Arctic）约 8.55 秒导出，独立解析 13 层；原厂 MCP 后期交接成功。独立 Web 审计画板完成一次真实整图生图，53.76 秒，1254×1254 原生图片回填为 600×450，PNG 和完整 sflowboard 已保存。receipt/hash 证明是新图；48,807 只读像素与全部 alpha 精确保持。未重复跑 4K。原来两份 board.json 校验值不变、Web 偏好已恢复。未发送系统键鼠输入；仅用只读窗口检查区分 SDK 保存失败与挂起。

证据 artifacts/ux-audit-20261110/{release-verified,browser-verified,handoff,real-task,real-pixel-oracle,original-boards-unchanged}.json。完整发现、首次失败、测试方式局限及下一轮设计项见 UX-Audit-2026-11-10.md。新建/打开时原厂连接有短暂重置，已保留为延迟绑定观察，不伪称为崩溃；SDK 直接覆盖正在打开的副本失败未计为正常保存通过。
# 2026-11-10 · 家里 B · 0.22.6

管理任务 8f19067556ab4bcfa41daefa4dd6a340 成功，PID 55020，部署 20261111-044502-310eccf60849405f8ddb2c6fbc9ece0c。原厂 Platform 验证原生与 Web 均为 0.22.6；Hillside-UX-Audit.3dm 已恢复，70 个对象，Modified=false。原生后期工具已打开并通过管理 MCP 显示 B 窗口；未发送系统鼠标事件。画板切换、窄侧栏布局及不同工具独立图标的验证见 Validation.md；用户已打开的网页需刷新加载新版静态文件。

## 2026-11-11 · 家里 B · 0.22.7 主题与八工具 UI

最终管理任务 0c34bf1bbd134a10aa76f1e83d46860c 成功，PID 25112，原厂 Platform 22801；插件部署 20261111-050434-f1248faaa38e43568ab24ad51692022b。实际原生版本 0.22.7、ChatKit ready=true，源码／部署／构建包匹配。旧测试 PID 26164 的退出由管理器确认为 NormalExit。

当前 Hillside-UX-Audit.3dm 已恢复并保持 70 对象、Modified=false，AI 素材工具已打开，B 窗口通过管理 MCP 显示。连续新建两次再打开案例，八工具重绑定且同 PID。主题、布局、按钮及无界面浏览器验证详见 Validation.md 和 artifacts/theme-ui-0227，未发送系统键鼠、未调用模型，也未改正式 Rhino。

## 2026-11-11 · v0.22.8 六通道导出与 Named Views

当前 B PID 19060，实例 2f293bc2170742139b65baba79b9c045；插件部署 20261111-060933-04e3afd785e0432e862e829346404434。原厂 Platform 路径 describe=0.22.8，正常 MCP 六通道导出及全八工具 new/new/open 通过，原案例 artifacts/ux-audit-20261110/Hillside-UX-Audit.3dm 已恢复，70 物件／未修改，PSD 页已选中。最终包 RHP 与加载部署 SHA256 均为 97F4B02015F4A88CFAF48C1C25CE93091E83EC8482EE4B12CB85C1FC75590903；最终原生编译采用管理器隔离构建，非之前 source/bin 中的旧布局二进制。

默认植物／阴影／材质贴图／Rhino Arctic／隐藏深度／隐藏材质颜色。新增颜色来源、material/object/all 分层、两级独立折叠与眼睛、当前视口建 Named View、双击同步改名及 Undo。真实示例 artifacts/export-0228/supported-final/01 Hillside Axon.psd，600×450，20 像素层。完整证据与两条额外探针的未确认退出见 Validation.md；这些异常不算测试成功，不声称原生所有退出已修复。未使用用户鼠标，未修改正式 Rhino、Platform 或新增 MCP 服务。

## 2026-11-11 · v0.22.9 季节与植物平面

最终 B PID 56416，实例 be7c46457ca0420899f0c2069cca666c，插件部署 20261111-073929-b5c761f04c2d480cb7f2e3c5ff386a02；describe=0.22.9。原案例 Hillside-UX-Audit.3dm 已打开，70 对象、未修改；原素材库／偏好恢复，案例预览切为 Rendered，设置区收起。包与实际加载 RHP SHA256：73593AFE9FFCE463B75C57B9DC4AC82825E8C16F3FAFC9178614D1754141ECE4。

已测试眼睛、设置、单素材八槽／复用、实际一张植物平面 AI 生图、夏冬材质／随机缓存、按视角判断季节合并以及全八工具 New/New/Open。季节试验库为隔离复制，未将合成冬季／圆形平面 fixture 写入正式库。真实 AI 图只在该隔离素材目录和生成执行器记录中，旧库不会自动批量生成。详细证据、测试误差与局限见 Validation.md、Seasons.md；全程原厂 MCP，没有新增 MCP 监听，也没有控制用户鼠标。

0.22.9 后续：已给原库案例河桦 Betula nigra 补齐真实夏季平面图；原先恢复的旧记录只有立面，导致高俯视继续回退。B PID 56416 当前 15 株已显示 plan，地面位置、树高、相机方向保持，文档未修改。无需重启。该实际素材补齐发生在恢复测试库之后，原库现在有此季节图片更新；早先“原库未加入季节图片”的测试结束记录只描述当时状态。

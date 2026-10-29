# 沙盒 B：v0.2 自动化验收

## 2026-10-29 v0.15 植物

仅 B，管理 19540 / Platform 22801。实际生成、复用、整库整理、散布、三种 PSD、独立像素 oracle、ChatKit 消息和原生 New 取消通过，见 Validation.md / Planting.md。已测试最近部署 `20261029-211213-3e93d98de4c84dd19f3b9d457b7366ec`，任务 `78cccbbf376b48388d9a4a8881c256dc`，PID 13876 / 实例 `1faece50a7d94f0fb079c64d5b78c0dd`。此部署的 PBR 透明在重叠俯视中仍有矩形缺口，已改写源码，不能将它当作最终显示完成版。

最终 Alpha 轮廓几何版已打包，`artifacts/plant-start-cutgeometry.json` 的 requestId `sceneflow-0150-native-cutout-preview-20261029` 尚未准入成功：系统提交内存约 97.5% 超过 94% 上限。B 已保存并 NormalExit（任务 `71dec6c74e194ec4beb921effef215fe`）；没有更改资源策略，没有操作正式 Rhino。释放内存后重试同一请求，查询 list_jobs 防止重复提交；加载后打开 `delivery.json` 模型，运行 Finish-PlantDelivery.py 并检查重叠原生预览，再执行真实 NormalExit / 重启，更新本段为实际结果。

示例 `artifacts/examples/Planting-v015/Planting-Demo-57912.3dm`、植物 PNG 及透视／俯视 PSD；唯一真实 Acer rubrum 已加入原库，合成夹具仍在独立测试库。最终 source/docs 和发布包完整，但 Native 轮廓预览还欠实机验证。

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

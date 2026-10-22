# 沙盒 B：v0.2 自动化验收

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

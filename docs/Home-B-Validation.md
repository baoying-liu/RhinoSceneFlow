# 家用电脑 B 通道验证

日期：2026-10-23（America/New_York）。项目位于 `C:/Users/liu12/Documents/00_DevProjects/C#/RhinoSceneFlow`，版本 v0.6.0。

## 安装与兼容性

家里的 B 固定 ID 是 `0d327c4c84f644f089b73834ffd93cfe`，与办公室 B 不同。管理 MCP 仍为 19540，原厂 Platform 实际测试端口从 Monitor 动态核对为 22801。只在此 B 添加 SceneFlow 项目及启用原厂 Platform；没有安装进正式 Rhino，也没有修改 A 通道或 Codex MCP 配置。

本机使用 .NET SDK 10.0.302，Rhino 插件仍以 net8.0-windows 编译。数组上的 `Reverse()` 在本机被解析为返回 void 的原地反转方法；Core 合成器和一个既有测试改为显式 `Enumerable.Reverse(...)`，保留原有遍历语义。Build.ps1 随后零错误、零警告，全部核心回归通过。独立 PSD 核心检查重合成误差最大约 1.486/255。

本机 `python` 是 Windows 应用别名，自动化使用 `py`，独立解码使用 `artifacts/verify-env/Scripts/python.exe`。校验环境安装 psd-tools 1.26.0，不是插件运行依赖。

首次构建加载任务 `35dc14f529854382935eb0655c5db6f9`；SceneFlow 部署 `20261024-024942-338fb32fd3214a7ba13107554e81a028`（目录使用 UTC 日期）。重启测试继续使用这份独立部署，原厂 Platform 以沙盒副本加载。

## 实测

在空白 B 文档重建球体、双曲面、马鞍面、圆环、带孔平面、地面及墙，共 8 个对象、3 个 Named Views。没有依赖未同步的办公室 artifacts，也没有恢复旧 3dm 的浮动视图表。

PID 46952 的完整功能与独立文件验证：

- 三张原生 Eto 预览卡片、添加 / 删除图层、空启用项拒绝、1K–8K 预设、两套独立深复制、细节相机 / 太阳、重开恢复通过。
- 320×200 的 Shadow / 材质组 / Shaded，以及 240×240 的 Shadow / Rendered 实际导出通过。图层顺序、RGB、混合模式和透明度独立解析通过；最大重新合成预乘 RGBA 误差约 1.906/255。
- 旋转 / 缩放后的原生着色前景与材质轮廓 IoU 约 0.9703。1200×720 分块接缝区域与整张参考一致，alpha 全图一致；另有 3 个非接缝边界像素 RGB 最大差 30/255，保留为曲面子采样数值差异。
- 两视图真实按钮异步导出成功，忙碌期间 UI 定时器响应 45 次。实际取消按钮取消 4096×2048 请求，未留下 PSD / tmp，文档状态保持。
- 8192×2048 材质通道实际导出约 3,581 ms；6 个材质像素图层，89,075,542 字节，所有图层与合成图独立解码通过。这不代表已验收 8K 阴影或 8K 原生渲染模式。
- 临时 Named View 相机写回后方向变化约 0.24776 弧度，数量与太阳恢复。

重复 `SetViewProjection` 后原生视锥有约 1e-14 的浮点正规化差异。最初按字符串精确比较会产生失败；测试改为对视锥参数取 10 位小数，仍严格检查相机位置 / 方向、尺寸、模式、太阳、对象数量、选择、视图列表和 Modified。没有通过修改模型状态绕过检查。

## 尚未排除的退出问题

PID 54048、46952 测试后出现退出，管理器未收到退出码或完整关闭握手，没有找到相应应用错误事件 / 转储；记录为 UnknownExit、Successful=false。46952 的三次开关检查在脚本返回时是零浮动视图、文档状态保持，但其后进程退出，**不能视为关闭稳定性验收通过**。已向用户确认是否手动操作窗口，原因未确定。44708 是管理器主动重启产生的正常退出，不计为故障。

退出证据分别保留 `artifacts/home-exit2.json`、`home-exit3.json`；完整功能报告在 `artifacts/rhino-B/workbench/`，包括 `report.json`、`verified.json`、`details-verified.json`、`async-verified.json`、`cancel-verified.json`、`8k-verified.json`、布局图及实际 PSD。失败迭代生成的 PSD 保留在各 run 子目录。

最终重新启动 B，保留测试模型及工作台供手动查看。启动命令为 `RhinoSceneFlowPanel`；默认手动输出目录设置为项目的 `artifacts/exports`。测试模型、最终 PID 与状态见 `artifacts/rhino-B/home/ready.json`。没有打开 Photoshop 或接管鼠标。

最终任务 `a33dfb0ce5af4c5a837adde50de95bcf`，PID 33348，实例 `b0b790c57ad342b7a2fd49dc9a0a0297`。`SceneFlow-Home-Ready.3dm` 已保存为当前文档，Modified=false；在此状态下再次验证滚轮事件、3 张预览、零浮动视图和 256×160 组合 PSD，Modified 仍为 false，文件独立解码通过。通过 B 管理器显式显示测试实例，工作台保留打开。

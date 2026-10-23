# RhinoSceneFlow

Rhino 场景表现工作流：**AI 素材 → 真实尺度材质 → 植物布置 → 视图分层导出 → 后期编辑**，由 Codex / Agent 编排。名称中的 Scene 表示材质与植物组成的场景，Flow 表示从 Rhino 到后期编辑的连续流程。

当前为 Rhino 8 / Windows v0.6.0 原型，已实现 **Eto 多视图卡片工作台**、独立尺寸与相机 / 太阳设置、可排序通道 / 显示模式 PSD 图层、混合模式与不透明度，以及原厂 Rhino-MCP-Platform 自动化适配。其余工作流模块尚未实现；不依赖 ComfyUI，不启动额外 MCP 服务。

项目位置：`00_DevProjects/C#/RhinoSceneFlow`，独立 Git 仓库；与 `00_DevProjects/C++/RhinoBIM` 在语言目录下层级一致。

## 首版行为

- 当前模型视图的平行 / 透视投影，按视口长宽比输出。
- 输出内容为不透明面对象的平涂色块，颜色来自所属图层的 `Layer.Color`；对象色、材质色、视口颜色覆盖不参与分组。
- RGB 完全相同的图层合并；中文图层名保留在 PSD 图层名称中。
- 所有颜色组共用深度缓冲，被其他组遮挡的部分不导出；完全不可见的组不生成空图层。
- 透明背景，2×2 子采样抗锯齿，8 位 RGB PSD，像素图层及合成预览。
- 支持 Mesh、Brep、曲面、Extrusion、SubD、嵌套块的面几何。块成员按自身所属图层分组，不推断父块颜色。
- 跳过隐藏对象与隐藏父图层；锁定面对象仍参与导出。
- 不修改模型、图层、选择、相机、显示模式或材质；临时文件写入成功后才替换目标 PSD。

色层导出使用专用 CPU 色块投影器，不输出贴图、光照、透明材质或植物 PNG 的 alpha；阴影通过独立命令导出。这些对象目前按不透明面处理。曲线、点、标注、文字和 Hatch 不导出，命令行会报告跳过类型及数量。网格精度可能与 Rhino 当前显示网格有差异。

当前不支持布局视图、关联裁剪平面的视图、自定义显示插件内容、渲染器效果和单独隐藏的子对象。布局与裁剪视图会明确拒绝。工程大坐标使用双精度相机投影，但实际 Rhino 相机对齐仍需实机验收。

## 构建

需要 .NET 8 或更新 SDK、Rhino 8（默认 `C:\Program Files\Rhino 8\System`）。插件运行于 Rhino 的 .NET 8 模式。

```powershell
.\scripts\Build.ps1
```

包输出：`artifacts/package/RhinoSceneFlow/`。保持该目录文件在一起，将 `RhinoSceneFlow.Plugin.rhp` 拖入 Rhino，或用插件管理器安装。构建脚本不修改注册表、不自动加载到已有 Rhino 会话。

非默认安装位置：

```powershell
dotnet build RhinoSceneFlow.sln -c Release '-p:RhinoSystem=D:\Rhino 8\System'
```

## 使用

批量导出工作台：执行 **`RhinoSceneFlowPanel`**。每个 Named View 一张预览卡片，可单独设置宽高（含 1K–8K 预设）、预览模式和刷新；双击进入相机 / 太阳细节页。下方配置 PSD 图层顺序、通道或显示模式、混合模式和不透明度。尺寸与图层配置分别复制粘贴。每个视图一个同名 PSD；重名先询问，不覆盖自动添加 001、002……。支持后台计算、进度、取消和配置恢复。完整说明见 [v0.6 工作台](docs/Workbench.md)，[v0.5 面板说明](docs/Export-Panel.md)保留为历史记录。

以下为保留的单视图命令用法：

1. 打开模型视图，设置视角和图层颜色。
2. 执行 `RhinoSceneFlowExportPSD`。
3. 输入输出宽度，默认 2048 像素；高度随当前视图比例计算。
4. 路径提示直接回车使用默认目录，或输入 `.psd` 绝对路径；不弹保存窗口。
5. 在 Photoshop 或其他兼容编辑器中查看分层。

输出上限 800 万像素、每边 8192 像素；默认 2048 分辨率也会消耗数百 MB 内存，复杂场景建议先以 512 像素验收。当前同步执行，大场景会暂时阻塞 Rhino 界面。

供后续 Codex/脚本调用的命令形式：

```text
_-RhinoSceneFlowExportPSD 1024 "C:\Exports\view.psd"
```

推荐 Codex 通过原厂 Platform 调用 [JSON API](docs/MCP.md)，省略路径即可自动导出到默认目录；返回绝对文件路径与图层信息。命令行也可接受默认路径。已有文件默认拒绝覆盖，API 显式传入 `overwrite:true` 才覆盖。

图层只包含导出视角中可见的区域，移动或删除前景后不会补出后景。抗锯齿边缘使用与当前图层顺序相关的条件透明度以保持合成一致；重新排序或隐藏图层时边缘像素可能变化。

## 代码结构

```text
src/RhinoSceneFlow.Core       相机投影、裁切、深度缓冲、颜色覆盖、PSD 写入
src/RhinoSceneFlow.Plugin     Rhino 命令、场景读取、导出服务、Platform JSON API
tests/RhinoSceneFlow.Validation  不依赖 Rhino 的核心回归验证及 PSD 样例
scripts                构建打包与独立 PSD 解码校验
docs                   设计边界、Rhino 实机验收清单
```

Core 与 Rhino SDK 解耦，可由后续命令、界面或 MCP 适配层共同调用。首版没有引入 C++ 或运行时第三方依赖，PSD 写入按 [Adobe 格式说明](https://www.adobe.com/devnet-apps/photoshop/fileformatashtml/)实现，当前使用未压缩通道；16 位、PSB、压缩、ICC 配置和材质分组留待后续。

v0.2.1 已修复马鞍形曲面的网格退化问题，并在球体、双曲面、圆环、带孔曲面上完成 1024 / 2048 像素实测，见 [复杂曲面报告](docs/Complex-Surfaces.md)。

## 验证

构建脚本运行核心验证，覆盖前后遮挡、绘制顺序、透视边界、相机近远平面裁切、透明背景、图层合成及取消时保护旧文件。

独立解码检查（开发环境可选，不影响插件运行）：

```powershell
python -m venv artifacts/verify-env
artifacts/verify-env/Scripts/python.exe -m pip install psd-tools==1.26.0
artifacts/verify-env/Scripts/python.exe scripts/Verify-Psd.py artifacts/validation
```

已完成的验证结果与未完成的实机项见 [验收清单](docs/Validation.md)。

## 沙盒 B 通道

开发测试固定使用 RhinoDevSandbox 的 B 通道，管理 MCP 端口 `19540`。`scripts/Sandbox-Mcp.py` 从本机配置读取凭据，调用固定通道端点，不把凭据写入仓库或输出。`scripts/Rhino-Mcp.py` 先查询 B 的活动 PID，再核对该实例 Monitor 回执，动态读取 Rhino 内部 MCP 端口；两种端口不能混用。

不要通过默认通道或 UI 当前页签推断操作目标，也不要直接修改本机 workspace.json。通道的构建、启动与备份重启统一通过管理 MCP 执行。

`scripts/Smoke-Rhino.py` 在 B 的空测试文档创建专用示例，验证真实命令导出、同色合并、遮挡、隐藏父图层与锁定对象；会保留示例模型供人工查看。完整测试记录见 `docs/Sandbox-B.md`。

## v0.3 独立阴影 PSD

**旧射线后端的已知准确性问题（2026-10-22）：存在可复现的近接遮挡漏影。** [问题复核与替代路线](docs/Shadow-Alternatives.md)包含反例及实验平面投影 PSD；平面投影实验尚未接入正式命令。

命令：`RhinoSceneFlowExportShadowPSD`。输入宽度和输出路径；回车使用默认路径，无保存对话框。自动化示例：`_-RhinoSceneFlowExportShadowPSD 1024 _Enter`。

输出透明背景、单一灰色、清晰边缘的 `Shadow` 图层；默认只输出投射阴影。模型需有实际接收阴影的表面。高级太阳方向、颜色、透明度和背光面开关通过 [MCP API](docs/MCP.md) 设置。默认优先采用启用且在地平线上方的 Rhino Sun，否则使用固定斜上方光源，报告记录实际来源。

几何查询采用固定版本 geometry3Sharp 1.0.324（Boost Software License 1.0）；参见 [第三方说明](third-party/README.md)。

实测记录、预览位置和曲面碎纹修复说明：[阴影验证](docs/Shadows.md)。

## v0.4 阴影体 PSD

新命令：`RhinoSceneFlowExportShadowVolumePSD`，回车采用默认 2048 像素宽度和默认路径。自动化：`_-RhinoSceneFlowExportShadowVolumePSD 1024 _Enter`；同一 MCP API 使用 `backend:"volume"`。旧阴影命令及省略 backend 的 API 仍使用旧射线后端，供对照。

新后端使用 CPU 软件 z-fail 阴影体，已恢复之前确认的近接漏影。v0.5.1 的面板及阴影体命令默认包含背光面和自身遮挡，只计算太阳直射光，不计算反射、间接光或 AO。预览采用 Eto 图片控件，避免创建额外的浮动 Custom view 窗口。v0.4 的方法与历史证据见 [阴影体后端](docs/Shadow-Volumes.md)。

v0.4.1 增加原始曲面复核，修正测试双曲面上的断续碎影，保留真实投射阴影；没有使用模糊或图像清理。含明暗边界的 9,049 个像素、36,196 个子采样与独立解析参考一致，原有 1,564 个 Brep 稳定区采样也通过。这个场景默认 2048 像素导出约 34 秒，较原型更慢。仍非任意模型的精度保证，SubD、极小特征等有限制。方法、前后对比及复核命令见 [准确性修正](docs/Shadow-Accuracy.md)。

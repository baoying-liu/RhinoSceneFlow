# RhinoSceneFlow

v0.22.0：[理解框画布与编辑历史](docs/Studio.md)，自动避让布局、实时分支连线、独立折叠、可撤销删除、Ctrl+Z／Ctrl+R、右键平移和列表滚轮。

v0.21.0：[可追溯图像工作流](docs/Studio.md)，原图只读、待生成白板、子级／同级、锁定更新、黄色草稿／紫色输入变化、可逆归档说明与备份容量管理。

v0.20.0：[AI 渲染工作台](docs/Studio.md)，列表／画布共用项目、标注与参考图、先整图再高清、工程包和中英文设置。命令仍为 `RhinoSceneFlowPostProduction`。

v0.19.0：[AI 后期真实生成](docs/PostProduction-Generation.md)，命令 `RhinoSceneFlowPostProduction`。支持单块测试、共享风格、批量修改、像素蒙版约束、融合和完整 PNG；可取消/继续、重试和对比结果。

v0.18.0 第一阶段：[AI 后期 Web 工作台](docs/PostProduction.md)，命令 `RhinoSceneFlowPostProduction`。支持 PSD 导入、图层与分块规划、GPT 描述助手；实际生图和融合尚未接入。

v0.17.4：[Plants List 与属性工具](docs/PlantsList-Properties.md)修正选择轮廓造成的悬空假阴影，保留真实植物阴影、单株动态预览与即时位置更新。命令：`RhinoSceneFlowPlantsList`、`RhinoSceneFlowProperties`。

Windows ZIP 分发包与离线安装验证见[分发说明](docs/Distribution.md)，接收者解压后运行 Install.cmd。

v0.16.4：植物生成支持对已检索到的官方物种页面逐一核实，补充 NParks / IFAS / Missouri Botanical Garden 的来源地址；记录访问失败原因，避免一个站点受限就阻断生成。

v0.16.3：隔离 ChatKit 的 Python 子进程，修复从 Rhino 继承内置 Python 环境导致的启动失败；首次安装仍运行 `scripts/Setup-ChatKit.ps1`。

v0.16.2：修复自定义箱式 UV 在 Brep 保存重开后误判失效；新增[山地小屋演示](docs/HillsideDemo.md)，用插件实际完成 AI 材质、透明河桦、参数化种植和分层 PSD。

v0.16.1：植物库和计算列表支持小图卡片／列表切换，中英文植物名称跟随设置，拉丁学名固定；AI 建议直接填入首次加入的默认参数。见 [种植界面](docs/PlantGroups.md)。

v0.16.0 新增[参数化种植对象](docs/PlantGroups.md)：多植物组合、独立布局／大小／镜像 Seed、连续点种、边缘衰减及承载面变化重算。v0.15 的[植物生成、植物库与种植](docs/Planting.md)和独立植物 PSD 通道继续保留。

v0.14.0 新增[材质随机去重复](docs/Randomization.md)：AI 自动建议、四种可调整方式、独立烘焙 Worker，以及真实尺寸和 PSD 材质变体合并。

Rhino 场景表现工作流：**AI 素材 → 真实尺度材质 → 植物布置 → 视图分层导出 → 后期编辑**，由 Codex / Agent 编排。名称中的 Scene 表示材质与植物组成的场景，Flow 表示从 Rhino 到后期编辑的连续流程。

当前为 Rhino 8 / Windows v0.16.1 原型，已实现 **五工具原生停靠工作区**（AI 素材、独立材质库、UV、植物库与种植、PSD）、AI 相似素材复用 / 分类标签整理、ChatKit 连续对话与参考图、真实尺寸材质与 UV、沿中心线管体 / xatlas 复杂曲面展开、多视图卡片 PSD 导出，以及原厂 Rhino-MCP-Platform 自动化适配。v0.13.3 增加[本地共享库并发保护与会话隔离](docs/Shared-Library.md)，文档切换修复见[生命周期说明](docs/Document-Lifecycle.md)。不依赖 ComfyUI，不启动额外 MCP 服务。

输入 `RhinoSceneFlow` 打开工作区。材质、UV、种植、PSD 可停靠或浮动，使用说明见 [Workspace.md](docs/Workspace.md)。

项目位置：`00_DevProjects/C#/RhinoSceneFlow`，独立 Git 仓库；与 `00_DevProjects/C++/RhinoBIM` 在语言目录下层级一致。

## 图层颜色通道（兼容首版）

- 当前模型视图的平行 / 透视投影，按视口长宽比输出。
- 输出内容为不透明面对象的平涂色块，颜色来自所属图层的 `Layer.Color`；对象色、材质色、视口颜色覆盖不参与分组。
- RGB 完全相同的图层合并；中文图层名保留在 PSD 图层名称中。
- 所有颜色组共用深度缓冲，被其他组遮挡的部分不导出；完全不可见的组不生成空图层。
- 透明背景，2×2 子采样抗锯齿，8 位 RGB PSD，像素图层及合成预览。
- 支持 Mesh、Brep、曲面、Extrusion、SubD、嵌套块的面几何。块成员按自身所属图层分组，不推断父块颜色。
- 跳过隐藏对象与隐藏父图层；锁定面对象仍参与导出。
- 不修改模型、图层、选择、相机、显示模式或材质；临时文件写入成功后才替换目标 PSD。

旧图层颜色通道使用专用 CPU 色块投影器，不输出贴图、光照、透明材质或植物 PNG 的 alpha；阴影通过独立命令导出。这些对象目前按不透明面处理。曲线、点、标注、文字和 Hatch 不导出，命令行会报告跳过类型及数量。网格精度可能与 Rhino 当前显示网格有差异。

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

选中物件后执行 **`RhinoSceneFlowMaterials`** 打开简洁材质窗口，底部选择应用到物件或其所在图层。可输入描述、添加参考图片、选择生成结果；应用时自动检查并补算真实世界 UV，显示计算 / 复用进度。尺寸与铺贴参数放在独立页面。“生成材质”直接启动本机已登录的 Codex，自动生成新图并入库；应用范围跟随当前选择，无选择时不会沿用旧物件。

**`RhinoSceneFlowPanel`** 中新增“通道 · 材质贴图”，默认同材质合并；也可按物件拆分，全部位于同一个“材质”PSD Group。复用已有真实 UV 与贴图物理尺寸，底色不含光照，阴影独立叠加。旧图层颜色配置保留。首版贴图通道限不透明位图 / 实体颜色；块、面级多材质、透明裁片暂不支持。详见 [工作台](docs/Workbench.md)。

**`RhinoSceneFlowWorldUV`** 可独立计算米制 UV，不分配材质；换材质复用有效 UV。完整材质库改用 **`RhinoSceneFlowMaterialLibrary`**。详细用法见 [材质与 UV 说明](docs/Materials.md)。

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


v0.11 ChatKit 对话、参考图片、xatlas 异步展开和新增 `material_chat_*` / `material_unwrap_*` API：[接入与使用说明](docs/ChatKit-Xatlas.md)。


v0.12 修复原生视口跨 UV 岛插值和内向测试模型的渲染朝向，新增 `RhinoSceneFlowTubeUV`：[管体与接缝 UV 使用说明](docs/UV-Continuity.md)。
## AI 后期 Web 工作台（v0.18.0 第一阶段）

命令 `RhinoSceneFlowPostProduction`，或工作区菜单「AI 后期 · Web 工作台」。先运行 `scripts/Setup-PostProduction.ps1`。支持独立导入 PSD、Rhino 文件交接、图层用途、分块预览、GPT 描述助手和 JSON 方案保存；实际生图、NetVips/OpenCV 融合与结果 PSD 尚未接入。详见 [后期工作台说明](docs/PostProduction.md)。

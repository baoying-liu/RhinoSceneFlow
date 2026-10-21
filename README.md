# RhinoPSD

Rhino 8 / Windows 插件。v0.1 原型从当前模型视图导出按**图层 RGB 颜色**分层的 PSD，作为后续 AI 材质、植物资产和 Codex 自动化工作流的起点。不依赖 ComfyUI，不自带 MCP 服务。

项目位置：`00_DevProjects/C#/RhinoPSD`，独立 Git 仓库；与 `00_DevProjects/C++/RhinoBIM` 在语言目录下层级一致。

## 首版行为

- 当前模型视图的平行 / 透视投影，按视口长宽比输出。
- 输出内容为不透明面对象的平涂色块，颜色来自所属图层的 `Layer.Color`；对象色、材质色、视口颜色覆盖不参与分组。
- RGB 完全相同的图层合并；中文图层名保留在 PSD 图层名称中。
- 所有颜色组共用深度缓冲，被其他组遮挡的部分不导出；完全不可见的组不生成空图层。
- 透明背景，2×2 子采样抗锯齿，8 位 RGB PSD，像素图层及合成预览。
- 支持 Mesh、Brep、曲面、Extrusion、SubD、嵌套块的面几何。块成员按自身所属图层分组，不推断父块颜色。
- 跳过隐藏对象与隐藏父图层；锁定面对象仍参与导出。
- 不修改模型、图层、选择、相机、显示模式或材质；临时文件写入成功后才替换目标 PSD。

这不是当前显示模式的截图分层。当前为专用 CPU 色块投影器，不输出贴图、光照、阴影、透明材质或植物 PNG 的 alpha；这些对象目前按不透明面处理。曲线、点、标注、文字和 Hatch 不导出，命令行会报告跳过类型及数量。网格精度可能与 Rhino 当前显示网格有差异。

当前不支持布局视图、关联裁剪平面的视图、自定义显示插件内容、渲染器效果和单独隐藏的子对象。布局与裁剪视图会明确拒绝。工程大坐标使用双精度相机投影，但实际 Rhino 相机对齐仍需实机验收。

## 构建

需要 .NET 8 或更新 SDK、Rhino 8（默认 `C:\Program Files\Rhino 8\System`）。插件运行于 Rhino 的 .NET 8 模式。

```powershell
.\scripts\Build.ps1
```

包输出：`artifacts/plugin/`。保持该目录文件在一起，将 `RhinoPSD.Plugin.rhp` 拖入 Rhino，或用插件管理器安装。构建脚本不修改注册表、不自动加载到已有 Rhino 会话。

非默认安装位置：

```powershell
dotnet build RhinoPSD.sln -c Release '-p:RhinoSystem=D:\Rhino 8\System'
```

## 使用

1. 打开模型视图，设置视角和图层颜色。
2. 执行 `RhinoPSDExport`。
3. 输入输出宽度，默认 2048 像素；高度随当前视图比例计算。
4. 选择 `.psd` 保存位置。
5. 在 Photoshop 或其他兼容编辑器中查看分层。

输出上限 800 万像素、每边 8192 像素；默认 2048 分辨率也会消耗数百 MB 内存，复杂场景建议先以 512 像素验收。当前同步执行，大场景会暂时阻塞 Rhino 界面。

供后续 Codex/脚本调用的命令形式：

```text
_RhinoPSDExport 1024 "C:\Exports\view.psd"
```

必须通过 Rhino 的脚本执行上下文调用，例如 `RhinoApp.RunScript`；脚本模式使用命令行路径，不弹保存窗口。指定的已有文件会在成功后被覆盖。

图层只包含导出视角中可见的区域，移动或删除前景后不会补出后景。抗锯齿边缘使用与当前图层顺序相关的条件透明度以保持合成一致；重新排序或隐藏图层时边缘像素可能变化。

## 代码结构

```text
src/RhinoPSD.Core       相机投影、裁切、深度缓冲、颜色覆盖、PSD 写入
src/RhinoPSD.Plugin     Rhino 命令、可见对象遍历、网格提取、保存对话框
tests/RhinoPSD.Validation  不依赖 Rhino 的核心回归验证及 PSD 样例
scripts                构建打包与独立 PSD 解码校验
docs                   设计边界、Rhino 实机验收清单
```

Core 与 Rhino SDK 解耦，可由后续命令、界面或 MCP 适配层共同调用。首版没有引入 C++ 或运行时第三方依赖，PSD 写入按 [Adobe 格式说明](https://www.adobe.com/devnet-apps/photoshop/fileformatashtml/)实现，当前使用未压缩通道；16 位、PSB、压缩、ICC 配置和材质分组留待后续。

## 验证

构建脚本运行核心验证，覆盖前后遮挡、绘制顺序、透视边界、相机近远平面裁切、透明背景、图层合成及取消时保护旧文件。

独立解码检查（开发环境可选，不影响插件运行）：

```powershell
python -m venv artifacts/verify-env
artifacts/verify-env/Scripts/python.exe -m pip install psd-tools==1.26.0
artifacts/verify-env/Scripts/python.exe scripts/Verify-Psd.py artifacts/validation
```

已完成的验证结果与未完成的实机项见 [验收清单](docs/Validation.md)。

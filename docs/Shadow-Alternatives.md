# 阴影准确性复核与替代路线

日期：2026-10-22。仅 RhinoDevSandbox B（固定 ID `1cee488700ad42f59492743cc4a2a3fe`），管理 MCP 19540，实际测试 PID 16208。原厂 Platform 的实际端口通过 Monitor/PID 核对。没有使用鼠标，没有修改正式安装，也没有启动其它 MCP 服务。

## 已确认缺陷

当前 v0.3 后端会漏掉真实投射阴影。为消除曲面背光分界碎纹引入的“顶点切平面误差法线偏移”可能将射线起点移动到遮挡物上方。旧版稀疏采样通过与干净预览不能排除这种失败。

B 通道中构造了两个尺寸相同、平移放置的实际 Rhino Mesh 测试：

- 接收面局部范围 x/y 为 ±2，z=0；上方遮挡片 x=[0.15,0.35]、y=[-0.5,0.5]、z=0.25。
- 指向太阳的方向为 `[1,0,1]`。从接收点 `(0,0,0)` 发出的光线明确穿过 `(0.25,0,0.25)`，位于遮挡片内部。
- 一个接收面使用平滑倾斜顶点法线，另一个使用面法线；实际面几何与遮挡片尺寸不变。
- 平滑法线案例的导出中心 alpha=0（错误缺失）；面法线案例 alpha=255（正确）。中心附近的切平面偏移约 1.1 模型单位，大于遮挡片高度 0.25，因此射线越过遮挡物。

这是一项可重复的合成反例，证明现有代码具有漏影机制；并不宣称它解释了用户模型中的每一个错误。记录在 `artifacts/rhino-B/alternatives/contact-counterexample-verified.json`，可视对照为 `missing-shadow-comparison.png`。

另外，默认 `includeFormShading=false` 会排除背光面，太阳未启用时采用固定备用方向。它们也可能造成“缺一块”和视口不一致的观感，需要在产品中明确光源与阴影范围；不能用这些差异掩盖上述真实漏影。

## 实际比较的替代方式

### 1. 平面几何投影：已跑通实验 PSD

使用 RhinoCommon `Transform.ProjectAlong(plane,direction)` 将投射物网格三角形沿光向投到有限地面；裁掉地面以下的投射物，裁剪接收面边界，用原有相机深度测试排除前景遮挡，保持 2×2 边缘覆盖。重叠三角形在采样上取并集，不使用法线偏移或图像修补。

实验输出：`artifacts/rhino-B/alternatives/planar-ground.psd`，1024×524、透明背景、单色独立图层；预览为 `planar-ground-overlay.png`。实验接收面为 z=-2，x=[-11,34]、y=[-7,7]。

在同一太阳、视角和有限地面的内部区域，与当前光线后端比较：44,081 个有效地面像素，阴影区域分别为 4,574 和 4,575 像素，只有 1 个二值采样差异，IoU 0.999781。此结果说明这组普通平面上的投影位置一致，不是解析 NURBS 精度证明，也不能覆盖接触反例。

优点是几何关系可核对，不需要法线抬升；后续可用 Clipper2 等做轮廓并集以导出矢量。当前原型只支持该有限平地，不支持双曲面、圆环内侧或任意曲面接收。投射物仍为网格近似，不能称为解析曲面精确阴影。正式扩展需处理接收平面集合、孔洞和相互遮挡。

官方 API：https://developer.rhino3d.com/api/rhinocommon/rhino.geometry.transform/projectalong

### 2. Rhino 原生视口开／关阴影差分：已试，尚不适合作为干净输出

使用离屏 `RhinoView.CaptureToBitmap(size,attributes)`，同一相机和白色材质，SceneLighting、太阳高度 40°、方位 200°、关闭天光、关闭软边与模糊，阴影贴图尺寸 4096，分别捕获开／关阴影。通过差分/亮度比例生成独立单色 alpha 预览。

原始视口及差分文件以 `native-SceneLighting-*` 保存。本次差分仍包含曲面上的碎点与透明度变化；不会把阈值化或模糊处理当作准确阴影。因此这一方式当前只作视口一致性对照，不自动替换正式导出。关闭照明的对照几乎没有可提取阴影，不能简单用无光照平涂模式取得原生阴影。

原生阴影同样有贴图分辨率、偏移、裁剪和背光分界的限制。官方文档列出相关质量/自遮挡设置，并未保证解析精度：

- https://docs.mcneel.com/rhino/8/help/en-us/options/view_display_mode_shadows.htm
- https://docs.mcneel.com/rhino/8/help/en-us/options/view_display_mode_lighting_scheme.htm

### 3. 重新设计几何可见性后端：建议用于任意曲面

这一项是后续实现建议，本轮没有接入新内核或声称已修复正式命令：

- 几何遮挡判定与平滑法线外观分离；使用接收命中点和明确的三角形 ID 处理自命中。
- 将数值最小距离与网格误差区分，避免按切平面误差任意抬升射线。
- 对 NURBS 设置可量化的细分误差，特别验收近接触、薄间隙、非平面四边形及孔洞。
- 使用独立解析交点/原始 Brep 测试，不重复后端相同的背光排除规则来证明所有阴影准确。
- 明确区分投射阴影、完整直射光不可达区域及指定接收面；读取 Rhino 的 CastsShadows/ReceivesShadows 属性，后续再支持 alpha 素材。

现有 geometry3Sharp 或 Embree 都可作为加速结构。Embree 是高性能光线追踪库，但替换库不会自动修复不正确的起点偏移、网格几何或光源策略。本轮未引入 Embree。

官方资料：https://www.embree.org/

## 修正太阳测试的验证缺口

发现旧 `Test-ShadowRhino.py` 的太阳角度设置没有使用 `Sun.BeginChange/EndChange`；因此原报告中“切到 45°”的验证不成立。旧测试只证明当时读取到的方向与显式方向输出一致，不能证明指定角度已应用。

已修正测试脚本，使用 Program 修改事务，断言方位角 135°、高度角 45°、手动控制以及方向 Z=-sqrt(0.5)。B 中的针对性重测通过，自动太阳与显式方向 PSD 字节相同；用 RenderSettings.Duplicate/恢复完整设置，并核对 Sun.Hash。证据在 `verified-sun-45.json`。这修复的是测试，不是当前漏影后端。

## 结论和复现

优先把平面接收阴影作为几何投影模式；任意曲面接收需要重做可见性与自命中策略。原生显示管线先保留为对照。当前 v0.3 命令仍有已复现的漏影缺陷，实验模式未注册为新命令或 MCP 操作。

按顺序在空 B 测试文档执行 `Research-ShadowNative.py`（读取已有 `Shadow-Test.3dm` 场景）、`Research-ShadowPlanar.py`，导出同视角的 `base-colors.psd`，再执行 `Research-ShadowContact.py`。外部运行 `Verify-ShadowAlternatives.py`。它的 `researchChecksCompleted=true` 表示研究检查完成，`currentBackendAccurate=false` 明确表示当前后端不能通过该接触精度案例。

所有生成文件保留在忽略的 `artifacts/rhino-B/alternatives/`。本轮修改研究脚本、测试及文档，未更改正式阴影算法。没有打开 Photoshop；文件检查来自独立 PSD 解码和预览检查。

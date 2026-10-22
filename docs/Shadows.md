# 独立阴影 PSD 验证（v0.3.0）

2026-10-21，通过 RhinoDevSandbox B、管理 MCP 19540，原厂 Platform `run_python` 实测。最终 PID 78996，实际 Rhino MCP 端口由 Monitor 核对；没有使用鼠标、正式安装或新的 MCP 服务。

命令为 `RhinoSceneFlowExportShadowPSD`，API 为 `export_shadow_psd`，参数见 [MCP.md](MCP.md)。输出透明背景单色 `Shadow` 像素图层，默认只包含投射阴影，可选包含背光面明暗。

## 测试场景与结果

两个球体、双曲抛物面、单叶双曲面、圆环体、带真实孔洞的裁剪平面、地面及墙面。阴影专用网格共 334,028 个三角形。四组用例均保持对象、选择、相机、显示模式、太阳设置及文档修改标记不变。

| 用例 | 宽度 | 稳定采样点 | 导出耗时 |
| --- | ---: | ---: | ---: |
| top | 1024 | 1175 | 1983 ms |
| perspective | 1024 | 867 | 981 ms |
| form | 512 | 816 | 889 ms |
| other-sun | 512 | 831 | 826 ms |

共 3,689 个稳定采样点全部通过，阴影阳性覆盖地面、墙面、球面及双曲面。参考算法使用 Rhino 原始 Brep/NURBS 的 `Intersection.CurveBrep` 与解析法线，不使用插件网格或 geometry3Sharp 作为参考；全图网格外再对各曲面投影范围加密采样，排除参考边界附近的不稳定像素。

独立 Python psd-tools 解码确认：一层 `Shadow`、所有像素层 RGB 一致、alpha 只包含 2×2 覆盖等级、透明背景、画幅与同视图色层一致、重合成最大预乘通道误差 0.502/255。对导出的阴影及叠加预览进行了目视检查，未见此前的三角碎纹。

附加检查通过：

- 默认 2048×1047 输出，10,482,544 字节，1,736 ms；独立解码尺寸、单色层与透明度通过。
- Rhino Sun 启用且高度 45° 时自动读取方向，结果与显式传入同方向的 PSD 字节完全一致；测试后恢复太阳设置和修改标记。
- 自定义 `#123456`、opacity 0.5 实机导出，外部解码确认 RGB 与最大 alpha 128。
- 原生命令 `_-RhinoSceneFlowExportShadowPSD 128 _Enter` 成功，新生成文件由独立解码器检查。
- 无效方向、颜色、透明度和 bias 被拒绝，不弹对话框。
- Core 验证解析平面投影、可见性、透视、画外投射物、大坐标平移、可选背光面、平滑法线、空阴影图层及球体背光分界无假阴影像素。
- 既有色层导出四视图复杂形体回归通过，6 个色层、61,762 三角形，原始曲面参考与球体面积检查保持通过。

## 发现并修复的问题

初版在双曲面和圆环体背光分界处出现三角碎纹。仅增大固定光线偏移并不能解决；诊断发现扭曲四边形的三角化误差和平面法线会将平滑曲面的背光误判为细小投射阴影。

修复包括阴影网格的长边细分、插值接收点法线、按局部顶点切平面偏差设置光线起点偏移。未对输出图像做模糊、阈值或形态学清理；所有透明度差异仅来自边缘覆盖和指定透明度。Core 增加独立凸球无投射阴影的完整像素检查。

沙盒最初保留的旧 PID 33084 已退出，退出码 0、无崩溃事件和新 dump；首次 build_test 因 UnknownExit 失败并保留记录，审核证据后通过管理 MCP 确认退出并显式启动新测试。最终成功任务 `5063d518b24549a8bf023f00e7fdbd7c`，部署 `20261021-191053-0f8e721f38b74cac9e201d5c6cf4e3e4`。没有把失败任务标记为通过。

## 文件与适用范围

生成文件均在忽略的 artifacts 下：

- `artifacts/exports/shadow-default-2048.psd`
- `artifacts/exports/shadow-top.psd`、`shadow-perspective.psd`、`shadow-form.psd`、`shadow-other-sun.psd`
- `artifacts/rhino-B/shadows/Shadow-Test.3dm`
- `artifacts/rhino-B/shadows/report.json`、`verified.json`
- 同目录 `perspective-shadow.png`、`perspective-overlay.png`、`top-overlay.png`
- `before-normal-fix/` 保留最初碎纹和失败采样证据。

结果为不透明网格近似的方向光硬阴影。接收面必须存在于模型中；没有隐式无限地面，不处理纹理 alpha、软阴影、透明材质、布局和裁剪视图。小于网格误差的薄间隙仍可能被偏移吞掉。同步导出会阻塞 Rhino 主线程；当前样例耗时不代表超大场景性能。未打开 Photoshop；文件验收来自独立 PSD 解码、重合成和预览目视检查。

## 2026-10-22 准确性复核：已确认漏影

v0.3 的切平面法线偏移在接触反例中会越过遮挡片，导致应为 alpha=255 的阴影变成 0。旧版采样通过不构成完整准确性保证；太阳角度测试也补上了 BeginChange/EndChange 和实际角度断言。详情、对照及替代方案见 [Shadow-Alternatives.md](Shadow-Alternatives.md)。当前后端尚未修复该漏影，不应将研究验证完成解释为后端精度通过。

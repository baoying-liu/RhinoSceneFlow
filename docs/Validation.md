# v0.2.1 验收清单

## 自动验证

- [x] .NET Release 编译通过，无警告。
- [x] 多颜色几何共用深度缓冲，前景遮挡后景。
- [x] 非共面场景反转三角形绘制顺序，像素归属保持一致。
- [x] 近裁切面穿越、侧面越界及完全位于近面背后的三角形。
- [x] 透视投影近远边界与视锥边界。
- [x] 透明背景与完全遮挡颜色组不生成图层。
- [x] 相邻色块抗锯齿后图层合成与参考像素一致（量化容差内）。
- [x] 取消写入保留原文件。
- [x] 独立 psd-tools 1.26.0 解码、Unicode 名称与图层重新合成检查；预乘 RGBA 最大差异 1.486/255。

## Rhino 沙盒 B 实机验收

- [x] Rhino 8 .NET 8 模式加载 v0.2 RHP，通过原厂 Platform API 和命令导出；不使用鼠标。
- [x] 红蓝 Mesh 面遮挡场景，俯视与透视导出；核心投影与 Rhino WorldToClient 误差小于 0.01 像素。
- [x] 两个同 RGB 图层合并，独立 PSD 解码确认图层名称与像素颜色。
- [x] 验证隐藏对象、父图层隐藏、锁定对象。
- [ ] 块实例及嵌套变换实机验证。
- [x] 球体、双曲抛物面、单叶双曲面、圆环及裁剪孔洞，平行和透视导出；原生 CurveBrep 参考采样检查通过。
- [ ] SubD 与大坐标模型实机验证。
- [x] 验证输出后文档 Modified、对象数量、图层属性、相机、显示模式、选择保持原状态。
- [ ] Photoshop 打开文件，不出现修复提示；确认中文名、透明背景、分层与合成画面。
- [x] 简单场景 512 px，复杂曲面 1024 / 2048 px 的导出与分层检查。
- [ ] 大场景内存、窄缝和共面对象专项检查。
- [ ] 在布局及裁剪视图中返回明确的不支持提示。
- [x] 默认目录持久设置与自动命名；MCP 导出不弹保存窗口；命令回车使用默认路径。
- [x] API 已有文件保护、非法宽度、错误视图、错误版本和不存在文档均返回失败。

真实文件已通过独立 psd-tools 解析与重新合成；Photoshop 应用本身尚未打开验证。完整记录见 [B 通道报告](Sandbox-B.md)。

v0.2.1 修复马鞍曲面被默认网格退化为单四边形的问题，见 [复杂曲面报告](Complex-Surfaces.md)。

## v0.3.0 独立阴影增量验证

B 通道 PID 78996 的最终版本通过独立阴影验收：3,689 个原始 Brep/NURBS 参考采样、单色与透明边缘、墙面和曲面接收、背光面开关、Rhino Sun、样式参数、原生命令及默认 2048 像素输出。阴影样例 334,028 三角形，默认导出 1,736 ms。色层复杂形体回归仍通过。

修复了平滑曲面背光分界的三角碎纹；完整方法、失败证据与限制见 [Shadows.md](Shadows.md)。本次通过外部 psd-tools 解码及预览检查，未打开 Photoshop，未发布到正式 Rhino。

## 2026-10-22 准确性复核：已确认漏影

v0.3 的切平面法线偏移在接触反例中会越过遮挡片，导致应为 alpha=255 的阴影变成 0。旧版采样通过不构成完整准确性保证；太阳角度测试也补上了 BeginChange/EndChange 和实际角度断言。详情、对照及替代方案见 [Shadow-Alternatives.md](Shadow-Alternatives.md)。当前后端尚未修复该漏影，不应将研究验证完成解释为后端精度通过。

## 2026-10-22 v0.4 阴影体增量

新增独立命令 `RhinoSceneFlowExportShadowVolumePSD` 和 MCP `backend:"volume"`。仅通过固定 B 通道部署，管理任务 `16674f059d1745cabbb734352b91fd2d` 成功加载 PID 26432，部署 `20261022-153951-18aa2cfcb65b41eda600206989d8e536`。未发布正式 Rhino，未使用鼠标。

`Build.ps1` 核心检查通过；真实 PSD 的 1,564 个原始 Brep 参考采样无不一致，近接漏影反例的新后端中心 alpha=255（旧后端仍为 0）。默认 2048×1047 导出约 9.1 秒。独立 psd-tools 验证单色、alpha、重合成及真实命令，未打开 Photoshop。实际 135°/45° Rhino Sun 的自动和显式方向 PSD 字节一致，完整渲染设置恢复。

同一网格的射线参考与阴影体透视结果仅 2 个像素相差 64 alpha；曲面分界仍有细碎纹理，不能将采样通过解释为全部像素或解析曲面精度保证。旧后端漏影未修复。详见 [Shadow-Volumes.md](Shadow-Volumes.md)，证据在 `artifacts/rhino-B/volumes/`。

## 2026-10-22 v0.4.1 原始曲面复核

阴影体后端自动复核曲面不确定采样和覆盖边界两侧，修正已复现的双曲面碎影。含明暗边界的独立解析参考检查 9,049 个像素、36,196 个子采样，0 不一致；另 2 个混合接收面轮廓像素通过。原始 1,564 个稳定区参考、近接漏影反例、样式、太阳、实际命令、默认输出和独立 PSD 解码重新通过。

最终 B 构建 PID 267632 的 PSD 与已验证结果字节一致。此场景默认 2048 输出约 34.1 秒，未做 GPU/C++ 迁移；未进入复核区的几何仍有网格近似限制，不能宣称任意模型精度保证。方法、前后放大对比与复核命令见 [Shadow-Accuracy.md](Shadow-Accuracy.md)。

## 2026-10-22 v0.5 Eto 面板与批量 PSD

`RhinoSceneFlowPanel` 在 B 的 PID 249608 实测。Named View 的 320×200、384×192、240×240 输出均通过；按视图独立尺寸、重名 002/003、显式覆盖、取消预检、材质/阴影单通道及合并通道、三种原生预览模式和尺寸刷新保留通过。7 个 PSD 独立解码和重合成，最大预乘 RGBA 差约 1.97/255；不同通道组合中的材质和阴影图层分别逐像素一致。

实际后台导出 352×224 成功，运行期间 UI 定时器响应 66 次；通过真正的 Eto 取消按钮取消 2048 输出，无 PSD 或临时文件残留。文档主视图、尺寸、图层及选择状态保持。没有操作鼠标或 Photoshop。完整复核脚本、报告路径与限制见 [Export-Panel.md](Export-Panel.md)。

## 2026-10-22 v0.5.1 直射阴影和预览窗口修复

本地 Build.ps1 完整构建和几何/投影/PSD 回归通过。Rhino B 的完整太阳直射阴影新增两个方向 8,552 像素独立参考检查，全部通过；纯投射阴影双曲面密集边界共 9,011 像素及两个混合接收面像素通过。两个真实近接反例的阴影中心均为 alpha=255。

当前场景同条件 1024×587、包含背光面及自身遮挡，旧完整计算 168,719 ms，新版 15,864 ms；601,088 像素 alpha 完全一致。旧版默认纯投射阴影与此基准不同，不能混为同一速度对照。后台面板 352×224 输出为 2,721 ms，UI 定时器在运行中继续触发；实际取消按钮取消 2048 输出后无 PSD 或临时文件残留。

方法、范围及证据见 [Shadow-Direct.md](Shadow-Direct.md)。所有运行仅在 B，PSD 通过独立解析器解码，没有打开 Photoshop、接管鼠标或部署正式 Rhino。

最终 UI 构建 PID 68104：七个真实批量 PSD 检查通过，最大重合成差约 1.77/255，各种通道组合中的材质及阴影层一致。Shaded/Rendered/Arctic 图片预览通过，实测预览 545×347。三次开关面板前后保持同四个视图、没有浮动视图，相机/尺寸/模式/视图名/选择/Modified 保持，测试结束面板关闭。证据：`panel/verified.json`、`panel/windows-verified.json`。

## 2026-10-23 v0.6 多视图工作台

本地 Build.ps1 构建与核心回归通过。新增 6 种混合公式、RGB 像素、文件夹混合 / 透明度、磁盘暂存、裁剪窗口和大尺寸写入验证；8192×2048 核心 RGB PSD（134,217,888 字节）经独立解码及首尾采样检查。

B 的 PID 227176 完成真实 Eto 多卡片、添加 / 删除空图层、启用空项拒绝、1K/2K/4K/8K 预设、独立复制粘贴及深复制、细节相机与太阳、关闭重开恢复和两张配置各异的 PSD 导出。psd-tools 验证实际图层顺序、材质分组、RGB 显示模式、混合 key 与透明度，独立重新合成最大预乘 RGBA 差约 1.906/255。旋转 / 缩放后的原生着色前景和独立材质轮廓 IoU 约 0.9703（原生边线和抗锯齿使其不是逐像素一致）。主视图、显示模式、太阳、对象、选择、视图列表及 Modified 保持。

1200×720 分块与原整张输出相比，接缝两侧带状区域逐像素一致，alpha 全图一致；全图有 1 个非接缝像素的 RGB 差 30/255，保留为曲面边界子采样数值差异，**不是全图字节一致**。检验脚本限制此类差异最多 4 像素、最大 64/255，另对接缝和 alpha 使用独立更严限制。证据保留在 `workbench/report.json`、`verified.json`，不对任意几何宣称解析精度保证。

B PID 265612：临时 Named View 写回通过，方向变化约 0.2478 弧度、数量和太阳恢复；真实两视图按钮后台导出成功，UI 定时器在忙碌时响应 89 次。真实取消按钮取消 4096×2048 请求，结果 cancelled=true、无 PSD / tmp 残留，状态保持。Eto 布局图显示两列卡片与分别可见的预览，无需接管鼠标。

实际工作台 8192×2048 材质通道导出 7,889 ms，6 个材质像素图层、89,075,902 字节，全部图层和合成图独立解码通过。该测试证明超过旧 800 万像素上限的工作台路径，不代表完整 8192×8192、多显示模式或阴影均已在此尺寸验收。

测试早期的 PID 205400、274748、227176 出现未能确定原因的实例退出，没有可归因的应用错误事件 / 转储；管理器保留 UnknownExit、Successful=false，未将退出记为通过。后续实例单独完成写回、异步、取消和 8K 验证。未打开 Photoshop，未修改其他通道或发布正式 Rhino。说明与复核脚本见 [Workbench.md](Workbench.md)。

补充：PID 265612 连续开关面板三次，文档视图保持、浮动视图为零；随后管理器关闭请求未收到完整握手，退出仍保留 UnknownExit。最终仅修改滚轮步进幅度，重新构建零警告 / 错误和全部核心回归通过，加载 B PID 175732。合成 +120/-120 Eto 滚轮事件分别产生 1.1 倍 / 恢复原缩放；四张卡片均加载、零浮动视图、256×160 阴影 / 材质 PSD 导出与文档状态保持通过。最终 PSD 再次独立解码，证据 `workbench/final-verified.json`。

家用电脑的独立 B 通道安装、.NET 10 兼容修正、真实分层 PSD / 后台导出 / 取消 / 8K 材质输出结果，以及关闭稳定性限制，见 [Home-B-Validation.md](Home-B-Validation.md)。

## 2026-10-26 公司 B 更新复核

同步 `c4e161b` 后重新构建和全部核心回归通过。更新部署 `20261026-134519-79366444417f4ae9ba5bff01b89e1781` 在公司 B 的 PID 108352 加载成功。4 张卡片预览、滚轮事件和 256×160 阴影 / 材质组合 PSD 通过，零浮动视图、文档状态保持；独立解析图层分组 / 阴影层及合成图，最大重新合成差约 1.773/255。记录保存在 `artifacts/rhino-B/office-update-20261026.json`。此次为安装后的短时验证，不替代之前完整测试，也不宣称退出稳定性问题已解决。
# 2026-10-26 v0.7 材质库验证

最终构建由沙盒 B 的 `build_test` 任务 `cce650d2025042a682a587340470158b` 完成，状态 Succeeded；包含 Build.ps1 核心回归，编译零警告。实际 Rhino PID 116016、原厂 Platform 22801，插件版本 0.7.0。

- `Test-MaterialLibrary.py` 最终证据：`artifacts/rhino-B/materials/run-0481b982/report.json`。原生 PBR 四通道、Normal 识别、平面重复 (1,1)、矩形箱式三个方向、圆柱弧长 / 高度、旋转、毫米 / 米 / 英尺 / 英寸、图层继承与新增对象同步、缩放后重映射、旧 RDK 材质 / 映射恢复、原 Mesh UV 保留、ZIP 跨库导入、真实 Eto 按钮及生成任务回填均通过；测试后原有 live object IDs 保持。
- 交替模拟两种材质的贴图隔离通过；显式 Rendered 图像 `materials/demo/rendered.png` 人工查看，石材地面与棋盘格物件正确区分。材质 Eto 内容截图 `materials/demo/panel-white.png` 人工查看，1110×900 无水平裁切。
- 原生 Undo 在命令退出后的 UI timer 执行，`materials/demo/undo-verified.json` 为 undo=true、fixtureExists=true、bindingRemoved=true。重现顺序：通过 Rhino-Mcp.py 分别运行 Test-MaterialUndoStart.py、Test-MaterialUndoApply.py、Test-MaterialUndoQueue.py；timer 回调后再运行 Check-MaterialUndo.py。这些脚本依赖已准备的自有 demo，期间不能插入其他模型编辑。
- `Test-MaterialExport.py` 导出 320×200 Named View PSD，保留相机、显示尺寸、太阳、Modified 及工作台原配置。`artifacts/verify-env/Scripts/python.exe scripts/Verify-MaterialExport.py` 独立解码通过：自上而下 Rendered / Shadow / 材质图层组，重组与内嵌预览最大误差 1/255。证据 `materials/demo/export-report.json`、`export-verified.json`；未通过 Photoshop UI 打开验收。
- 使用内置 imagegen 真实生成 1×1 m 浅灰石灰岩颜色图，完成 Agent 回填和入库；源图 SHA-256 为 `99253F390405434F3519C50CE1C99368885DCF1B20E1D1521E9C7AA6B26469FE`。完整提示词与源图保存在 `artifacts/materials/source/`。

保留了早期失败证据：BasicMaterial 丢 PBR、TextureMapping JSON 无法还原、RenderMaterial=null 抛异常、同名贴图串图以及旧 UI 布局裁切。最终实现分别使用 FromMaterial、显式 MappingSnapshot、材质索引恢复、资产唯一文件名与独立布局行修复。没有把这些失败版本记为通过。旧 v0.6 测试实例曾 UnknownExit；原记录仍保留，不能据此宣称旧退出问题已修复。

当前范围及限制见 [Materials.md](Materials.md)：AI 需 Agent 实际处理；物理尺寸需标定；变形后手动重映射；不包含复杂自由曲面无畸变展开、块实例映射或自动云服务。
# 2026-10-26 v0.8 米制 UV 与简洁窗口

Build.ps1 核心回归通过，编译零警告 / 错误。B 最终使用部署 `20261026-210109-7bc0cdfa2e96465482ea80502974a8b9`，实际加载任务 `b500a553d5f64083b5353de89eafc2cb` Succeeded，Rhino PID 26764、Platform 22801。

- `Test-WorldUv.py`：`artifacts/rhino-B/worlduv/2a21a042/report.json` complete=true、liveIdsRestored=true。独立计算保留材质、1 米 UV 增量 (1,1)、600×300 mm 贴图原生模拟重复 (1.6666667,3.3333333)、换材质复用同一记录、手动改映射 / 同边界内部网格编辑 / 缩放 / 单位改变的失效识别、恢复无 UV 原状、混合图层有效 / 无效 / 缺失对象、参考图复制及 running 状态均通过。
- 调整后的 `Test-MaterialLibrary.py`：`materials/run-019a5ab7/report.json` 全部通过，保留 PBR 四通道、平面 / 矩形箱式 / 圆柱、英制换算、图层继承、恢复和贴图隔离回归。它现在把米制 UV 与材质物理尺寸组合检查，不再将原始 UV 当作图片重复次数。
- `Test-MaterialQuickUi.py` / `Check-MaterialQuickUi.py` 实际 Eto 操作通过：`worlduv/quick-ui-verified.json`，图层中计算 1 个、复用 1 个，显示 1/2、2/2 和最终 100，两个对象均 ByLayer。取消首步前不修改 UV；生成任务复制参考图片、显示 Agent 阶段、完成回填后自动选中新资产，证据 `worlduv/quick-generation.json`。回填测试复用先前生成的真实图片，不称为新一轮模型生成。
- 首轮原生 Undo 四阶段通过；同时断言 WorldUv 记录随应用撤销。证据 `materials/demo/undo-verified.json` 与 `worlduv/quick-generation.json`。逐物件 UI 流程是多个撤销记录，非整个批次一次撤销。
- `Test-MaterialExport.py` 及独立 `Verify-MaterialExport.py` 再次通过，320×200 PSD 重组最大差 1/255；未打开 Photoshop。Rendered 示例人工查看，石材和矩形棋盘重复正确；580×740 的生成页 / 铺贴页文件截图人工查看，无裁切，应用范围在底部。文件 `worlduv/quick-generation-white.png`、`quick-mapping-white.png`。

保留迭代失败：初版 FromMaterial 丢贴图 UVW，已通过对子纹理 SetRepeat 修复；首次变换测试错误地使用复制模式 False，断言失败并遗留一个自有副本，随后仅按该测试唯一标记清理，改用替换模式 True 后重跑通过。

部署任务 `c8afe7b7d41e43cfa950749515779078` 曾 CloseTimedOut。通过 computer-use 技能检查到 Rhino 退出阶段隐藏的 Update Available 对话框；选择 No 后进程退出，未强杀、未安装更新。保留失败任务及关闭证据，待退出后重新提交 test 才实际加载成功；没有把超时任务标为通过。

撤销复测限制：随后同一实例的重复 SDK / timer 撤销返回 false，等待 recording inactive 和改用脚本命令均未解决。失败证据 worlduv/undo-retry-failure.json，不能认定是定时器竞争，也不能把首轮通过扩展为重复撤销全部通过。保留 Check-MaterialUndo.py 的 WorldUv 移除断言；未修改产品原生撤销机制。显式恢复按钮及材质 / 映射还原测试通过。

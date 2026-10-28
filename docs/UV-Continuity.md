# v0.12：原生接缝 UV 与连续管体展开

`RhinoSceneFlowUnwrap` 保留 xatlas 自动分区；新命令 **`RhinoSceneFlowTubeUV`** 用于有中心线的等径管体侧面。先选择管体，再选择中心线。材质面板“尺寸与铺贴”页也有“沿中心线展开管体”按钮。之后正常应用材质，材质尺寸仍由材质库的宽 / 高控制；换尺寸不重新展开。

管体展开以中心线弧长和截面周长作为米制坐标，采用平行移动框架并分配闭合框架旋转，显式拆开周向和闭合长度接缝。需要位于管体中心的有效曲线；99% 顶点的半径偏差超过 5% 时拒绝，变径管、端盖和非管状曲面应分开处理或使用其他映射。闭合长度 / 周长不一定是贴图周期的整数倍，因此收口仍可能错相；不通过偷偷改变材质物理尺寸来强行对齐。弯管内外侧存在不可消除的局部长度差，不能承诺全球无缝或等距。

## 原生显示修复

旧版把 atlas 作为 custom mesh projection 套回原始共享顶点网格。Rhino seamCheck 不处理这种映射的分岛，原生视口会跨岛插值，而旧 PSD 路径直接读 atlas UV，因此两边不一致。v0.12 使用原生 `RenderMeshProvider` 返回完整的接缝顶点、米制 UV 和平滑法线；活动通道 1 使用表面参数坐标，避免再投影。PSD 使用同一份网格。

源 Mesh / Brep / SubD 不替换，不把 NURBS 转成文档网格。可以确认的单个闭合内向壳体只在拥有的渲染快照中修正绕序和法线；原几何保留供恢复与对照。开放面和多壳体不盲目整体翻转。原生渲染回调只返回 UI 线程准备的独立快照，不遍历活动文档几何。

分岛网格存储在一个未被占用的辅助映射通道（从 1000 起查找），与通道 1 一并校验 hash；用户已有通道不覆盖。v2 记录包含源 CRC、单位、两个映射 hash 和渲染朝向修正状态。恢复材质 / UV 会删除仍能确认属于本插件的辅助通道。源几何、映射、中心线在计算期间改变会拒绝提交；取消保留原记录。v0.11 的 xatlas 记录标记失效，需重新展开后才允许带材质导出。

保存重开后需要加载 SceneFlow 插件以重建原生渲染网格；辅助数据本身保存在 3dm 中。渲染缓存按材质变化更新，短暂保留旧快照以跨过原生回调，随后释放。改动仅部署于测试 B，不自动覆盖正式 Rhino。

## 原厂 Platform MCP

仍通过 `RhinoSceneFlow.Plugin.McpApi.Execute(JSON)`，不增加 MCP 服务：

```json
{"apiVersion":1,"operation":"material_unwrap_start","document":1,"objects":["OBJECT-ID"],"method":"tube","guideId":"CURVE-ID"}
{"apiVersion":1,"operation":"material_unwrap_status","jobId":"JOB-ID"}
{"apiVersion":1,"operation":"material_uv_renderer","document":1,"objectId":"OBJECT-ID"}
```

`method` 默认 `xatlas`。管体结果额外报告 lengthMeters、radiusMeters 和 radiusVariation；所有结果报告实际面积、岛数、拉伸和朝向修正。`material_uv_renderer` 不传 objectId 时返回缓存状态，传入时检查原生渲染管线实际返回的 UV、法线和体积。

## 实测

2026-10-28，办公室 B，Rhino 8.35：76,800 面三叶结在连续管体模式约 **4.228 秒**，1 个连续区，中心线约 86.478 m，半径约 0.700 m；拉伸中位 1.0717、95 分位 1.1790、最大 1.3641。UV 面积 380.351 m²、三维面积 380.182 m²，不作面积归一化伪造精确相等。xatlas 仍是多岛方案，不宣称砖纹跨岛连续。

Mesh 与 NURBS 球体的原生返回网格 / 存储展开网格 UV 误差 0、法线误差 0、体积为正，源 geometry CRC 不变。真实砖纹视口与材质 PSD 对照、独立 PSD 解码、六次材质切换、600×300 mm / 1×1 m 原生材质重复、取消、中心线变化、映射变化、恢复及预留通道保护通过。实际重开 3dm 后，文档 serial 从 268435457 变为 268435458，三个对象的原生 UV / 法线检查仍全部为 0。

脚本：`Test-/Check-/Finish-UvContinuity.py`、`Export-/Verify-UvContinuity.py`、`Test-/Check-/Finish-UvContinuityGuards.py`、`Finish-UvContinuityRestore.py`、`Check-UvContinuityReopen.py`。证据在 `artifacts/rhino-B/uv-v012`；预览和分层 PSD 在 `artifacts/examples/UV-v012`。未打开 Photoshop，未使用鼠标。

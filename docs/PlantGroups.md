# 参数化种植对象（v0.16）

## v0.16.1 缩略图与名称

植物库和计算列表默认显示小方块缩略图，可分别切换为带小图的列表。每项固定显示拉丁学名，下方显示当前语言名称；较长名称省略显示，悬停可看完整文字。列数跟随侧栏宽度，少量素材自动缩短容器，高数量素材在容器内滚动。支持拖入、双击加入、键盘方向选择和 Enter 加入；重复加入只选中原项。

顶部名称语言选择“跟随 Rhino / 中文 / English”，只控制植物名称，不翻译整个工作区。两个显示模式及语言按插件设置跨文档保存。新生成素材保存中英文名称，旧素材由后台名称补全任务处理；科学身份、来源、图片、尺寸、间距与外观 revision 不变。名称更新使用共享库锁、目录 revision 检查及事务日志。未能确定俗名时使用原学名，不编造物种名称。

AI 建议直接作为首次加入组合的参数默认值，例如建议间距；库内不再显示建议说明段落。已有组合的手工参数不会因名称补全、切换语言或显示方式而重置。库保持展开，允许连续拖入多种植物；选中已有种植对象时才自动收起库，优先显示组合参数。

缩略图按当前可见范围绘制，每个浏览区最多缓存 64 张 160 像素预览。新建／打开文件时先解绑并释放自身画布与图片、字体，不处置 Rhino 注册的面板宿主。

种植工具以单个 Rhino 网格对象保存组合参数、承载面 ID、手工附着信息和最后显示结果；不是将独立点简单打组。网格用于整体拾取和包围范围，conduit 显示真正的相机朝向植物。选择整个对象后，种植页自动打开并加载参数。原有 v0.15 独立点继续显示／导出，不自动改变旧模型。

## 使用

1. 在植物库搜索，拖入下方植物组合，或点击“添加到植物组合”。可重复添加不同素材。
2. 点击组合项，编辑比重及中心间距（米）。生成时两株最小中心距离为两项间距的平均值。比重是候选采样权重；边界和间距限制可能改变最终数量比例。
3. 设置密度（株/m²），选择 Brep、Surface 或 Mesh，点击生成。数量为承载面的网格面积乘密度，包含手工补种；受约束未填满时报告实际数量。开启“突破植物间距”可忽略距离限制。
4. 选中种植对象再点击连续点种，或运行 `RhinoSceneFlowPlant`。在承载面连续点击，Enter／Esc 结束；新建的纯点种组合初始密度为 0，已有组合保留密度。点种采用当前组合选中项，先约束到承载网格，再附着到原面。植物始终世界 Z 轴朝上，不沿坡面法向倾斜。
5. 改密度时保留全部手工植物，并补足自动植物；手工数量超过目标时保留它们。选中时手工为青色、自动为橙色 Alpha 轮廓。

Layout Seed 只影响自动候选位置／植物种类；Size Seed 和 Mirror Seed 是独立、稳定的散列流，也控制手工植物。最小／最大比例默认 0.75 / 1.5；两个滑块默认区间分别 0.5–1、1–2，可展开修改。两个比例不可倒置，区间必须有效。

边缘衰减有米制距离、0–1 强度、5 个可编辑节点的分段线性曲线（含图示），可分别作用于自动密度和所有植物大小。手工植物不因密度衰减被删除或移动。自动密度使用概率加权候选并尝试达到总目标，预算耗尽会报告不足。距离为到承载网格裸边的三维最近距离，**不是曲面的测地距离**；闭合面没有裸边，衰减不起作用。尺寸衰减保留最小 1% 因子，避免零尺寸植物。

新生成植物的 AI 识别步骤同时给出建议间距与依据，来自实际核实物种的生长习性／成熟冠幅，并明确用途假设，不把 PNG 宽度当成株距。已有资产默认 1 m 并明确提示手动调整，不伪造历史 AI 建议。

## 承载面更新与保存

面几何 CRC、参数、种植对象变换或单位发生变化后，约 0.45 秒稳定等待，再用 owned 数值快照在后台计算，同时最多两个布局 Worker。新修改取消旧任务，旧结果不提交。工作线程不访问 RhinoDoc、Brep 或 Mesh；快照、附着与显示代理提交都在 UI 线程。计算中显示上次结果，PSD 要求最新结果已完成。拖动过程中不逐帧重算完整布局。

手工植物在 Brep／Surface 保存面索引与 UV，在 Mesh 保存原面顶点与重心权重。相同拓扑变形后重新求附着位置；不可靠的拓扑变化尝试在上次位置附近 5 cm（或 10 倍模型容差）重附着，否则保留并报告待重新附着。删除承载面保留最后结果，重新关联时显式将手工点投影到新承载面。原对象 ID 关联不递归跟踪块内面，也不自动猜测被删除对象的替代品。

参数编辑有 Rhino Undo 记录；异步显示代理是派生缓存，提交不添加独立 Undo，也不改变原文档 Modified 状态。曲面撤销会重新计算相应布局。JSON 参数和附着记录在对象属性中，最后结果和可序列化变换数据在几何中，随 3dm 保存／重开；图片仍引用本地库，未嵌入模型。整体复制后仍关联原承载面，可单独移动／重新关联。

限制：最多 64 种／10000 株，50 万布局尝试，承载面最多 200 万三角面。不是无限密度或无碰撞体积模拟；间距为基部中心的三维距离，不是冠幅碰撞。旧独立点的 Rhino Scale 限制保持，整组的原生几何变换通过自定义变换记录处理。对承载面和种植对象同时施加变换时，应检查结果或重新关联，避免重复的关联变换。

PSD 继续使用原植物通道，单株／按学名／全部合并及阴影规则不变。种植代理排除在非植物材质和阴影接收几何之外。

验证入口：`PlantLayoutValidation`、`Test-PlantGroups.py` / `Check-PlantGroups.py` / `Advance-PlantGroups.py`。B 的真实结果以 Validation.md / Sandbox-B.md 为准。


## 0.23.2 development: avoidance objects and exclusion regions

This development build is tested only in sandbox B; it is not a published release.

The planting carrier remains a Surface, Brep or Mesh. Trimmed Breps/Surface objects
are meshed with Rhino's trimming boundaries; holes are not filled for sampling.
A separate `PlantGroupSpec.exclusionObjects` GUID array (maximum 256) references
avoidance geometry. `exclusionClearanceMeters` is a nonnegative metre distance.
`exclusionMode` is `geometry` by default, or explicitly `footprint`.

- Geometry mode uses the existing geometry3Sharp acceleration library with owned
  triangle snapshots: inside tests for closed solids, and 3D surface distance for
  open geometry. References may be Breps, surfaces, Meshes or extrusions.
- Closed planar curves define XY exclusion regions. Footprint mode explicitly
  projects all selected geometry into world XY. This is not the default for
  multilayer/overhead/roof geometry. Trim holes in supplied Breps/Meshes remain holes.
- These tests concern plant placement anchors and safety distance, not precise
  trunk/foliage volumes. Increase clearance for canopy separation. Surface distances
  follow Rhino's render-mesh approximation, not exact NURBS distance evaluation.
- Existing manual/custom specimens are retained and reported as conflicts; new
  manual points inside an exclusion are rejected without ending continuous placement.
- Reference geometry changes/deletion invalidate layout caches. Deleted references
  stop blocking and are reported. Clearances use metres across document units.
- Target density retains its existing definition against carrier mesh area;
  exclusions/spacing can limit achieved count. Exclusions never override spacing.
- Layout workers build owned acceleration data without Rhino SDK access. Single-plant
  edits validate references without rebuilding all obstacle meshes; cached queries
  preserve the existing immediate editing path.

The planting/properties tool provides selection, clear, clearance and mode controls
in a collapsed exclusion section. APIs reuse `plant_group_create` / `plant_group_update`
and return `exclusionConflicts` / `missingExclusions` from `plant_group_state`.

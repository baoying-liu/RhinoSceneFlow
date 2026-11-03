# 山地小屋演示

按用户提供的景观轴测参考图搭建简化示例，不是建筑施工模型。原始家里 B 版本在 `artifacts/examples/Hillside-Retreat`，主文件 `SceneFlow-Hillside-Retreat.3dm`；公司电脑于 2026-11-02 在公司 B 重新搭建，文件位置见下文。几何通过原生 Rhino SDK 创建，资产生成、分类、UV、材质应用、参数化种植及 PSD 均通过已发布的 SceneFlow 服务/API 完成，没有绕过插件设置贴图或伪造生成图片。

## 公司电脑复现（2026-11-02）

公司 B，RhinoSceneFlow v0.17.0，PID 59052 / 原厂 Platform 22801。完整文件：`%LOCALAPPDATA%/RhinoSceneFlow/Demos/HillsideRetreat/SceneFlow-Hillside-Retreat-Office.3dm`（166,373,343 字节）。三个建筑体量、48×40 m 起伏场地、69 个非植物对象、15 株河桦（其中 4 株手工补种），保持原示例的构成。公司缺少家里生成的原始素材，因此通过插件重新生成同类素材，并非同一批像素图片。

重新生成的资产：河桦 `24fcecbe-4ea8-48f0-8b73-332d0d6ab3e8`（988×1501，真实透明 PNG，表现高度 8 m）；草地 `80494bfb-52ea-41dd-be58-041f6290e1a2`（4×4 m）；雪松 `da8e6581-808e-48ca-8e77-f63885689032`（1.2×2.4 m）；矿物饰面 `9ae7a964-8866-4e7c-a225-d3f38fb970ab`（2×2 m）。AI 自动分类／标签及随机化建议保留，草地为 stochastic，雪松为 structured。五种辅助纯色色板仍为插件导入资产，不能称为 AI 生成。素材在公司当前配置库 `artifacts/rhino-B/workspace013/library` 及其 Plants 子目录，模型不是脱离素材库即可移机的独立包。

可编辑组合 ID `73fb8208-d869-4935-bb7e-23a6e81e4641`，承载网格 ID `e1f56af3-1ddc-4fe4-8746-05756428d128`。B 中已选中该组合并打开 Plants List。双击列表组合进入属性；在视口中选择单株可测试自定义。承载区位于图层 `11 Planting - Editable Region`。为得到 15 株，密度按承载网格实际面积计算；5.5 m 是年轻树演示布局设置，不是成熟树推荐株距。

三个 Named Views 与原示例同名，PSD 面板预设 1600×1200，植物按物种、阴影正片叠底 45%、真实材质与 Arctic。新建独立显示模式 `SceneFlow Demo - Rendered` 使用白底，保留原厂显示模式。`PSD/01 Hillside Axon.psd` 已实际导出 1200×900 / 11 个像素层，耗时 11,039 ms；psd-tools 独立解码确认底到顶为 Arctic、材质、Shadow、植物。`Office-final-preview.png` 是重开后的原生预览，`PSD-composite.png` 是独立 PSD 合成。

原 OneDrive 项目路径保存两次失败，保留了旧几何文件，没有当作成功或崩溃；改存上述本机短路径后，原生 Save、再次覆盖保存及重开通过。根因未确认，不把路径相关的观察当作已修复插件问题。Open 的 HTTP 10054 后重新连接，确认同一 PID、新文档序列、69 个有效米制 UV、15 株／4 手工、三视图与七工具 error=null，Modified=false。只读窗口检查使用 computer-use，恢复查看测试窗口但未使用鼠标，未操作正式 Rhino。

证据位于同一示例目录：`geometry.json`、`tree-job.json`、`tree-state.json`、`asset-queue.json`、`planting.json`、`applied.json`、`ready.json`、`export.json`、`psd-verified-office.json`、`office-reopened.json`。失败保存／请求日志保留为 `artifacts/office-hillside-*.log`。新增脚本 Start/Check-HillsidePlant、Setup-HillsideViews、Style-HillsideDemo、Checkpoint-HillsideDemo、Export-HillsideDemo、Reopen-HillsideDemo 和 Ready-HillsideOffice 可用于分阶段复现；不要在已有模型中重跑只接受空文档的建模脚本。

约 48 × 40 m 起伏基地，三个错落建筑体量、入口平台、弯曲步道、地形切边和等高线。69 个非植物对象均有米制 UV 和有效材质绑定。建筑玻璃采用不透明示意色板，不模拟室内、透明玻璃或反射。等高线是建模时生成的展示几何，不会自动跟随后续地形编辑；植物承载区与中央草地为相邻不重叠网格。

插件实际生成三种材质：4 × 4 m 草地、1.2 × 2.4 m 竖向雪松、2 × 2 m 米白矿物饰面；AI 自动分类、标签、随机化建议与纹理准备均保留。基地切边、窗框、玻璃、步道和等高线是通过插件导入/应用的纯色色板，不能称为 AI 生成材质。

通过原有 AI 对话流程生成一份河桦 `Betula nigra` 透明 PNG（8 m 年轻标本为表现尺寸估计），并自动入植物库。实测资料见 [NC State 植物页面](https://plants.ces.ncsu.edu/plants/betula-nigra/)。15 株共用一个参数化组合，4 株为手工补种；组合间距 5.5 m 是本示例年轻植株的演示设置，并非成熟树栽植规范。

## 操作

- B 中运行 `RhinoSceneFlow` 打开工作区；选中树木组合自动载入种植参数。测试密度、Layout/Size/Mirror Seed、比例与边缘衰减。
- 图层 `11 Planting - Editable Region` 是实际承载网格；编辑其顶点可测试附着与自动重新计算。几何改变后，材质 UV 可能需要使用 UV 工具重新计算再导出。
- 三个 Named Views：`01 Hillside Axon`、`02 Arrival Perspective`、`03 Planting Overview`。PSD 工具已配置各 1600 × 1200，植物按物种合并、阴影正片叠底、真实材质按材质合并、极地模式。
- `PSD/01 Hillside Axon.psd` 是实际 1200 × 900 导出示例；`01 Hillside Axon.png` 等为原生预览，`PSD-composite.png` 是独立 PSD 解码合成。

材质与植物保存在本机共享库 `Documents/RhinoSceneFlow/Materials`（植物子目录 `Plants`），并不全部嵌入 3dm。复制到另一台机器时需要同时迁移素材并重新关联路径；不要仅带走模型后宣称可离线移机使用。

## 证据与复现

`initial.json`、`tree-job.json`、`tree-state.json`、`asset-queue.json` 记录真实生成任务和资产 ID；`geometry.json`、`planting.json`、`applied.json` 记录对象/参数/绑定；`ready.json`、`verified.json`、`reopened.json` 记录 UV、重开、工具页与独立 PSD 检查。预览及文件解码不代表已经在 Photoshop UI 中验收。

脚本顺序：`Build-HillsideDemo.py`（只接受空文档）→ 原有 `material_chat_start` 树木任务完成 → `Advance-HillsideAssets.py` 串行生成三种贴图 → `Plant-HillsideDemo.py` → `Apply-HillsideAssets.py`（等待随机贴图完成后再次调用）→ `Finish-HillsideDemo.py`。本轮视图、密度微调、导出与重开脚本保留在 `artifacts/home0161`。示例文件已有时不直接重跑建模脚本。

此次实测同时发现并修复 v0.16.1 自定义箱式映射的持久化哈希问题：保存 Brep 后原生映射网格归档字节变化，导致 UV 被误判失效。v0.16.2 对数值顶点/面/UV/法线及映射变换做语义指纹，仍检测真实修改；旧的有效指纹保留兼容校验。旧的已经失效记录仍须正常重新计算一次，不跳过安全检查。

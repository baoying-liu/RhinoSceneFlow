# 山地小屋演示

按用户提供的景观轴测参考图搭建简化示例，不是建筑施工模型。示例在 `artifacts/examples/Hillside-Retreat`，主文件 `SceneFlow-Hillside-Retreat.3dm`；仅使用家里测试 B。几何通过原生 Rhino SDK 创建，资产生成、分类、UV、材质应用、参数化种植及 PSD 均通过已发布的 SceneFlow 服务/API 完成，没有绕过插件设置贴图或伪造生成图片。

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

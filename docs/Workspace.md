# SceneFlow 侧栏工作区（v0.13）

输入 `RhinoSceneFlow` 打开工作区。四个工具注册为 Rhino 原生 Eto 停靠标签：材质、UV、种植、PSD。可像 RhinoBIM V2 一样停靠、浮动、组合，位置由 Rhino 保存。插件加载只注册面板，不主动弹出窗口。右上角 `⋯` 可把四个工具放回同一容器。只在首次出现无法使用的 200×200 浮动容器时设置可用尺寸，已停靠及已调整的正常容器不强制移动或缩放。

原有命令仍可使用：`RhinoSceneFlowMaterials` 打开材质侧栏（无需预先选择），`RhinoSceneFlowMaterialLibrary` 展开材质库，`RhinoSceneFlowPanel` 打开 PSD 标签。`RhinoSceneFlowWorldUV`、`RhinoSceneFlowUnwrap` 和 `RhinoSceneFlowTubeUV` 保留独立几何命令。

## 材质

主页面保留 ChatKit 对话、图片输入、进度、应用范围和应用按钮。选中对象在每次点击应用时重新读取；该次队列冻结目标，后续选择不改变正在处理的任务。下次点击使用新的选择。应用范围为当前物件或其直接所在图层；缺失真实尺寸 UV 先补算，已校准且有效的 UV 复用。高级设置收起贴图实际宽高；默认 1×1 米只是明确的初始参数，不是 AI 从图片测量的结果。

“优先复用相似的已有材质”默认开启。本机 Codex 根据最新请求、参考图和现有材质的名称 / 分类 / 标签 / 描述判断，最多返回六个高相关候选；没有合适候选才继续生成。候选需由用户选择和应用，不自动替换物件。讨论不强制复用；修改既有方案不替换成无关库资产。关闭开关可明确要求全新生成。检索失败会明确报告，不偷偷产生额外图片。

“材质库 ›”在宽工作区中显示侧边伴随页；窄停靠栏中使用同一内容的库页面，可返回助手。列表每行显示实际贴图平均颜色的圆形色样、名称和分类。选择后显示贴图及 Rhino 原生 RDK 材质球预览；预览是独立内容，不向文档添加材质、对象或视口。原生预览失败时保留贴图并可重试。

支持关键词搜索与分类、分类内标签的交集筛选。可编辑名称、分类、标签及导入图片。AI 生成或编辑完成后自动命名、归类及生成属性标签，优先沿用已有词汇。若分类服务失败，新图片仍保存到“待分类”，避免重新生成浪费图片额度。标签是外观描述，不是假定测量的粗糙度或 PBR 贴图。

“AI 整理”读取整库快照，统一名称、同义分类和标签；不删除 / 合并资产，不改图片、尺寸或文档绑定。提交前校验全部 ID 和版本；库发生变化时拒绝旧方案。写入失败恢复原始元数据。单独 `catalogRevision` 记录名称 / 分类 / 标签修改，不改变材质外观 `revision`，因此整理不会让之后应用的相同材质产生额外外观版本。

## 其他工具

UV 工具提供自动平面 / 箱式、xatlas 复杂曲面及中心线管体入口。真实尺寸与接缝限制沿用 UV-Continuity.md。种植仅作明确占位。

PSD 工作台改为单列 Named View 卡片，适应侧栏；保留每视图预览、显示模式、像素预设 / 复制、PSD 图层配置 / 复制、混合模式、不透明度、材质合并策略及批量导出。双击预览进入当前侧栏内的相机 / 太阳细节页，不新建原生 RhinoView。渲染、阴影和 PSD 服务未改算法。

## 自动化

仍通过原厂 Rhino-MCP-Platform 的 `run_python` 调用 `RhinoSceneFlow.Plugin.McpApi.Execute(JSON)`，没有新增 MCP 监听器。`material_workspace_open/status/group`、`material_shelf_open`、`material_tool_select/settings/apply`、`material_update_labels`、`material_catalog_organize/status/cancel`、`material_native_preview` 覆盖新交互。完整参数见 MCP.md。

旧 `material_quick_open/status` 和 `material_open_panel/panel_status` 改为工作区别名；返回结构是新的工作区 / 工具状态，旧的反射窗口测试不再适用。几何、材质与 PSD 数据 API 保持兼容。

本机 Codex 负责语义检索和标签，未引入 ComfyUI、额外 API key 或外部分类服务。关闭面板 / Rhino 只取消自己的任务和子进程，不结束 Rhino。Rhino 8 现代浮动面板默认尺寸适配集中在 WorkspacePanels.cs，使用与 RhinoBIM V2 类似的版本检测反射边界；不涉及原厂 Platform 的内部实现。

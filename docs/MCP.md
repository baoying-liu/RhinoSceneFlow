# 原厂 Rhino-MCP-Platform 接入

## v0.13 停靠工作区与材质检索 / 分类

以下操作继续经过 `McpApi.Execute`；请求带 `apiVersion:1`。涉及模型 / UI 的请求带当前 `document`（RhinoDoc RuntimeSerialNumber）。

| operation | 参数与返回 |
| --- | --- |
| `material_workspace_open` | `page:materials\|library\|uv\|planting\|export`，默认 materials；返回五个原生 panelId、dockBars、工具状态；v0.13.2 工具的 `error` 字段记录文档重建错误，正常为 null |
| `material_workspace_status` | 只读；材质状态包含 selected、job、lastJob、scope、reuseSimilar、shelf |
| `material_workspace_group` | 显式将四个工具组合进材质面板所在原生容器 |
| `material_shelf_open` | `visible?:bool`，默认 true 打开独立材质库工具；false 切换 AI 工具 |
| `material_tool_select` | `assetId`，`page?:materials\|library`，默认 materials；同步两个工具的待应用材质 |
| `material_tool_settings` | `page?:materials\|library`、`scope?:object\|layer`、`reuseSimilar?:bool`；应用范围在两个工具间同步 |
| `material_tool_apply` | `page?:materials\|library`，默认 materials；从本次实时 Rhino 选择启动 UV / 应用队列；状态中 busy 与 status 跟踪 |
| `material_library` | `query?`、`category?`、`tag?`，三个条件取交集 |
| `material_update_labels` | `assetId,name,category,tags:[string],expectedCatalogRevision?:int`；仅增加 catalogRevision，不改变外观 revision；预期版本不符时拒绝过期编辑 |
| `material_catalog_organize` | 启动实际本机 Codex 整库整理，返回 id / running |
| `material_catalog_status` | `jobId`；running / completed / failed / cancelled |
| `material_catalog_cancel` | `jobId`，取消本任务，提交前不修改分类 |
| `material_native_preview` | `assetId,path:绝对PNG路径`，Rhino 原生 RDK 球体缩略图，不添加文档内容 |

`material_chat_start` 新增 `reuseSimilar?:bool`（默认 true）。有可信匹配时任务 completed，`matches:[{id,score,reason}]`，`material:null`，不生成图片；无匹配时才进入原有生成链。分数阈值 0.82，最多六项。任务生成 / 编辑图片后自动命名、归类和生成标签，分类失败仍保存新图并明确标为待分类。无新图的普通讨论仍是 `material:null`。检索 / 分类用本机已登录 Codex，不新增 API key 或 MCP 服务。

兼容命令：RhinoSceneFlow、RhinoSceneFlowMaterials、RhinoSceneFlowMaterialLibrary、RhinoSceneFlowPanel。旧窗口状态别名现在返回侧栏状态；旧的窗口反射用例需改用工作区接口。具体流程见 [Workspace.md](Workspace.md)。

## v0.9 自动生成与当前选择

`material_generation_start`：`asset`、`prompt`、可选 `referenceImages:[绝对路径]`。实际启动本机 Codex 子进程，使用现有 ChatGPT 登录调用内置 image_gen，新 PNG 经校验后自动入库。返回 running 任务，后续用 `material_generation_jobs` 查询。失败为 failed 并附 error，取消为 cancelled。不需要外部 Agent 手动 complete。

`material_generation_executor`：只读返回执行端类型、可执行文件发现结果及当前运行任务，不导出账号凭据。路径不正确 / 未登录 / 无图片工具 / 服务失败 / 超时会明确失败；不会用旧图作为结果。非标准安装可通过继承的 `RHINOSCENEFLOW_CODEX` 指定 exe。`material_generation_cancel` 会同时取消该任务自己的 Codex 子进程。

原 `material_generation_request` / progress / complete 保留给手动 Agent 交接，其 pending 不会自动消费。两个入口用途不同。参考 [官方非交互 CLI 文档](https://learn.chatgpt.com/docs/developer-commands)；本机实测版本 0.164.0-alpha.11.1，stdio JSONL，无新增 MCP 端口。

`material_quick_open` 可传 objects 以同步 Rhino 当前选择；面板不再固定启动对象。后续面板应用 / UV / 恢复动作每次读取当前选择，无选择时拒绝操作；点击后该次队列范围固定。低层 `material_apply` / prepare_uv API 仍严格按显式 objects / layers 执行，不隐式替换调用者提供的 IDs。

## v0.7 材质操作

v0.8 新增：`material_prepare_uv`（document、objects 或 layers、可选 mapping / force / preview）独立计算或检查米制 UV；返回 computed、reused、metersPerUv=1。force=true 显式重算并采用新的 mapping；默认复用有效记录，失效时沿用记录中的投影设置。`material_uv_status`（document、objects）返回有效性和记录。`material_apply` 现在自动补算并返回 uvComputed / uvReused，原接口保留。

`material_quick_open`（document，可选 objects，否则当前选择）打开简洁窗口并同步当前选择（v0.9 起不固定启动目标）；`material_quick_status` 返回 busy / progress / history 等。旧 `material_open_panel` 仍打开完整材质管理窗口。

`material_generation_request` 可增加 `referenceImages:[绝对图片路径]`；任务返回复制后的参考路径。`material_generation_progress`（jobId、stage，1–200 字）将任务置为 running 并更新阶段；running 与 pending 均可完成 / 取消。后端未提供的生成百分比不应伪造。Agent 必须实际读取参考图片后调用支持图像输入的生成工具。

下列请求仍包含 `apiVersion:1`。涉及文档的操作需要 `document`；对象与图层目标只能选择一种。所有资产尺寸、映射偏移和原点均为**米**，与面板使用 mm 区别。

| operation | 参数与结果 |
| --- | --- |
| `material_library` | 可选 `query`；返回 directory、assets 和 contract |
| `material_configure` | `directory`：库的绝对路径，保存偏好 |
| `material_import` | `asset` 元数据、`files` 图片路径字典；返回新资产 |
| `material_update` | `asset`：从库读取的完整资产，保留其 revision / catalogRevision，修改名称 / 尺寸 / 参数后提交；版本不符拒绝覆盖，图片不替换 |
| `material_preview` / `material_apply` | `document`, `assetId`, `objects:[GUID]` 或 `layers:[GUID]`，可选 `mapping`；preview 只预检，不渲染也不修改文档 |
| `material_inspect` | `document`, `objects:[GUID]`；返回绑定、可恢复状态及尺寸过期提示 |
| `material_remap` / `material_restore` | `document`, `objects:[GUID]` 或 `layers:[GUID]`；图层 remap 同步新增对象 |
| `material_pack` | `assetId`, `path`：新的绝对 ZIP 路径，不覆盖 |
| `material_unpack` | `path`：ZIP 绝对路径，校验后导入为新资产 |
| `material_generation_request` | `asset`, `prompt`：建立 pending 任务 |
| `material_generation_jobs` | 列出任务，包括状态与生成提示词 |
| `material_generation_complete` | `jobId`, `files`：Agent 生成后回填本地图片，返回入库资产 |
| `material_generation_cancel` | `jobId`：取消 pending 任务 |
| `material_open_panel` / `material_panel_status` | `document`：打开材质面板 / 查询面板状态 |

`files` 支持 `baseColor`（必填）、`roughness`、`normal`、`metallic`，值为绝对 PNG / JPEG 路径。Normal 使用 OpenGL RGB 约定。示例通过下文的原厂 Platform 调用入口执行：

```python
asset = {'name': 'Limestone', 'category': 'Stone', 'tags': ['floor'],
         'widthMeters': 1.0, 'heightMeters': 1.0,
         'roughness': 0.8, 'metallic': 0.0, 'recommendedMapping': 'plane'}
request = {'apiVersion': 1, 'operation': 'material_import',
           'asset': asset, 'files': {'baseColor': r'C:\Textures\limestone.png'}}
response = json.loads(McpApi.Execute(json.dumps(request)))
assert response['ok'], response
asset_id = response['result']['id']
request = {'apiVersion': 1, 'operation': 'material_apply',
           'document': int(__rhino_doc__.RuntimeSerialNumber),
           'assetId': asset_id, 'objects': ['OBJECT-GUID'],
           'mapping': {'mode': 'plane', 'alignment': 'continuous', 'axis': 'auto',
                       'rotation': 0, 'offsetUMeters': 0, 'offsetVMeters': 0,
                       'originMeters': [0, 0, 0], 'checker': False}}
print(McpApi.Execute(json.dumps(request)))
```

`mode` 为 auto / plane / box / cylinder，`alignment` 为 continuous / object，`axis` 为 auto / x / y / z。AI 任务必须由外部 Agent 读取、调用图像工具并回填；pending 不代表已生成。具体映射范围、人工标定与材质显示模式导出见 [Materials.md](Materials.md)。

RhinoSceneFlow v0.10.0 不启动 MCP 服务，不监听额外端口，不修改 Platform 私有实现。使用已安装的 Rhino-MCP-Platform 的 `run_python` 工具，在 Rhino UI 线程调用公开入口：

```csharp
string RhinoSceneFlow.Plugin.McpApi.Execute(string requestJson)
```

这与本工作区 RhinoBIM 的 Platform 适配方式一致。Platform 的 `tools/list` 保持原有工具；RhinoSceneFlow 操作通过下面的 `describe` 自描述发现，不作为额外顶层 MCP 工具注册。

## 调用示例

把以下脚本作为原厂 `run_python` 的 `script` 参数。不使用鼠标、保存窗口或 `RhinoApp.RunScript`。

```python
import clr
import json
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi

request = {
    'apiVersion': 1,
    'operation': 'export_psd',
    'document': int(__rhino_doc__.RuntimeSerialNumber),
    'width': 2048
}
print(McpApi.Execute(json.dumps(request)))
```

必须使用 Platform 注入的 `__rhino_doc__`，不要把 `scriptcontext.doc` 或其他 Rhino 实例的文档序列号作为目标。导出要求显式文档序列号，不能隐式回退到另一个活动文档。

## 操作

| operation | 必填参数 | 可选参数与行为 |
| --- | --- | --- |
| `describe` | `apiVersion: 1` | 返回版本、接口契约、支持范围 |
| `status` | `document` | 返回默认目录、当前视图 ID、视口尺寸、投影类型 |
| `configure_export` | `directory` | 绝对路径；保存为插件偏好，导出时创建目录 |
| `export_psd` | `document` | `width` 默认 2048；`path` 默认自动生成；`viewportId` 校验活动视图；`overwrite` 默认 false |
| `open_panel` | `document` | 打开/激活本地 Eto 批量面板，返回状态 |
| `panel_status` | `document` | 返回面板视图、尺寸、模式、忙碌状态及上次结果；未打开时为 `open:false` |
| `named_views` | `document` | 返回稳定 id、名称及默认宽高 |
| `workbench_settings` | `document` | 返回每视图配置、可导出显示模式及混合模式 key |
| `configure_view` | `document`, `viewId`, `settings` | 部分更新配置，嵌套对象合并，图层数组整体替换；保存并同步已打开面板，不改 Named View |
| `export_workbench` | `document`, `directory` | `views:[GUID]` 可选，省略使用配置中勾选视图；`collision` 默认 `number`，支持 `overwrite` / `cancel`；按独立配置导出含显示模式、分组、混合模式和不透明度的 PSD |
| `export_named_views` | `document`, `directory`, `views:[{viewId,width,height}]` | `channels` 默认 `["material","shadow"]`；`collision` 默认 `number`，也可为 `overwrite`、`cancel` |

所有请求均需要 `apiVersion: 1` 和 `operation`。返回统一为：

```json
{"apiVersion":1,"ok":true,"result":{}}
```

## v0.6 工作台配置示例

先调用 `workbench_settings` 获取视图 ID 与显示模式 ID，再更新指定视图：

```python
request = {
    'apiVersion': 1, 'operation': 'configure_view',
    'document': int(__rhino_doc__.RuntimeSerialNumber),
    'viewId': 'NAMED-VIEW-GUID',
    'settings': {
        'width': 2048, 'height': 1280,
        'layers': [
            {'kind': 'shadow', 'blend': 'mul ', 'opacity': 60},
            {'kind': 'texture', 'textureGrouping': 'material', 'blend': 'norm', 'opacity': 100},
            {'kind': 'display', 'mode': 'DISPLAY-MODE-GUID'}
        ],
        'camera': {'yaw': 10, 'pitch': -5, 'zoom': 1.2},
        'sun': {'useDocument': False, 'azimuth': 135, 'altitude': 45}
    }
}
print(McpApi.Execute(json.dumps(request)))
```

`layers` 从上到下对应 PSD 堆叠。`kind` 为 `shadow`、`texture`（真实贴图）、`material`（兼容图层色）或 `display`，显示模式需提供 `mode`。混合 key 为 `norm`、`mul `（末尾空格必须保留）、`scrn`、`over`、`dark`、`lite`；不透明度为 0–100 的整数，`enabled` 默认 true。

相机支持 `yaw`（±180°）、`pitch`（±89°）、`zoom`（0.01–100）、`panX/Y/Z`（模型单位），均为相对已保存 Named View 的覆盖。太阳高度 0.1–90°、方位 0–360°。`mode`（顶层）只控制卡片预览；PSD 中的显示模式由每个图层条目控制。工作台每边 64–8192 像素，PSD 原始像素数据约 2 GB 上限；旧单视图 / `export_named_views` 的 800 万像素限制保留。

`export_workbench` 同步执行，适合可等待的 Platform 调用；面板按钮使用 UI 捕获加后台计算，并支持取消。工作台设置与使用方式见 [Workbench.md](Workbench.md)。

失败返回 `ok:false` 与 `error.code`、`error.message`，不会弹出交互提示。常见错误包括 `platform_unavailable`、`wrong_thread`、`unsupported_version`、`document_not_found`、`unsupported_view`、`invalid_request`、`export_failed`。

导出结果含绝对文件路径、尺寸、颜色图层名称、面对象及三角形数量、跳过类型、耗时、文档和视图 ID。材质透明度、纹理、光照、曲线、文字不在当前色块导出范围内。

## 默认目录

插件首次使用的通用默认值是系统文档目录下的 `RhinoSceneFlow/Exports`。本项目沙盒 B 通道将其设置为项目的 `artifacts/exports`。

省略 `path` 会生成带时间戳和随机后缀的文件名，避免覆盖。提供现有路径时，必须显式指定 `overwrite:true` 才覆盖；临时文件完成后才替换目标。

## Codex 自动检查

仓库提供 `scripts/Rhino-Mcp.py`，只向沙盒管理 MCP `19540` 查询 B 通道，再核对其 Monitor PID，使用该实例实际端口执行原厂工具。它不会更改现有 Codex MCP 配置。

`scripts/Smoke-Rhino.py` 生成演示并通过本 API 导出；`scripts/Verify-RhinoPsd.py` 在外部用 psd-tools 解码真实文件，检查尺寸、颜色图层、遮挡、透明背景以及图层重合成。外部检查不启动 Photoshop，也不需要鼠标。

## v0.3 阴影导出

`export_shadow_psd` 使用同一 Platform 入口和显式 `document`，共享 `export_psd` 的 `width/path/overwrite/viewportId` 规则。返回 `result.export` 为原有导出报告，另有 `toSun/lightSource/color/opacity/includeFormShading/bias/empty/backend`。

```python
request = {
    'apiVersion': 1, 'operation': 'export_shadow_psd',
    'document': int(__rhino_doc__.RuntimeSerialNumber),
    'width': 2048,
    'toSun': [-0.3, -1, 1],
    'color': '#5A5A5A', 'opacity': 1.0,
    'includeFormShading': False
}
print(McpApi.Execute(json.dumps(request)))
```

`toSun` 为世界坐标下**表面指向太阳**的向量，内部归一化。省略时，启用且位于地平线上方的 Rhino Sun 优先，否则使用固定方向 `[-1,-1,2]`；实际来源和方向写入报告。导出不启用或修改 Rhino 太阳。`color` 默认 `#5A5A5A`，`opacity` 范围 `(0,1]`。无渐变、软阴影、环境光遮蔽；2×2 超采样仅控制边缘覆盖。

v0.5.1 的 `backend:"volume"` 默认 `includeFormShading=true`，背光面与遮挡阴影填为同一阴影色，只计算太阳直射光，不计算反射、间接光或 AO。显式 false 可导出纯投射阴影；旧 `ray` 后端仍默认 false。双面网格的法线按相机方向统一；不依赖对象原始法线方向。

接收面必须是模型中实际可见的表面，支持地面、墙、曲面；不自动创建无限地面。隐藏对象不参与投射或接收；透明材质仍视为不透明网格。曲面使用阴影专用细分网格近似，仍非解析 NURBS 阴影。`bias` 可指定正数（模型单位）以控制数值自相交误差，默认 `max(ModelAbsoluteTolerance*0.001,1e-7)`。旧 `ray` 后端还按局部顶点切平面偏差移动光线起点，已确认会越过邻近遮挡面而漏影，不能将该启发式视为可靠修复。

无阴影时仍输出一个完全透明的 `Shadow` 图层，`empty=true`。阴影和色层使用同一相机、画幅及尺寸，保持视图不变时可直接对齐。PSD 内只有独立 `Shadow` 像素层，可在后期调整。

## v0.4 阴影体后端

在 `export_shadow_psd` 请求中加入 `"backend":"volume"`。省略时保持旧版 `"ray"`；未知值返回 `invalid_request`，不回退。结果中的 `backend` 标识实际执行的后端。`describe` 当前返回版本 0.5.1 和该参数。Named View 面板及批量 API 默认使用包含背光面的 volume 后端。

```python
request = {
    'apiVersion': 1, 'operation': 'export_shadow_psd',
    'document': int(__rhino_doc__.RuntimeSerialNumber),
    'backend': 'volume', 'width': 1024,
    'toSun': [-0.3, -1, 1]
}
print(McpApi.Execute(json.dumps(request)))
```

`volume` 使用 CPU 软件 z-fail 阴影体，沿光方向建立封闭体并计数。v0.4.1 自动复核曲面上的不确定采样及阴影覆盖边界两侧：重新查询原始 Brep/曲面和真实法线，尊重裁剪环并修正相切交点，不沿平滑法线偏移。平滑法线用于筛选复核位置和可选本体明暗。Mesh/SubD 仍使用实际三角网格，未复核区域仍由网格计算。

`bias` 保留模型单位含义：阴影体比较相机深度时用作容差；原始几何复核中光线起点仅沿太阳方向前进该距离，查询容差更小。返回 `result.export.surfaceRefinements` 为本次原始几何查询的采样数量；色层与旧射线后端为 0。此字段为追加字段，API 仍为 1。其余样式、默认路径、太阳方向来源及空 PSD 规则不变。

原生命令 `RhinoSceneFlowExportShadowVolumePSD` 固定使用 `volume`。新方案较慢，当前同步执行。此后端没有增加 MCP 服务、端口或顶层工具。测试证据与限制见 [Shadow-Accuracy.md](Shadow-Accuracy.md)；[Shadow-Volumes.md](Shadow-Volumes.md)为 v0.4 原型记录。

## v0.5 Named View 批量导出

`export_named_views` 每个视图写一个 PSD，选中的材质色层和阴影层组合到同一文件。此旧接口的 material 通道是图层色；真实贴图请用 export_workbench 的 texture 通道。`views` 使用 `named_views` 返回的 id 作为 viewId，宽高均显式给出；按请求画幅调整相机，保持文档主视图不变。

API 不弹覆盖窗口，默认重名编号；显式 `collision:"overwrite"` 才允许覆盖已有原名文件。同一批次的清理后同名视图仍编号避免互相覆盖。`collision:"cancel"` 在遇到已有文件时整体拒绝预检，返回 `ok:false`，不写入文件。所有尺寸、视图、通道先预检；运行中单项失败则记录该项错误并继续其余视图。

`result.files` 含 `viewId/name/path/ok/width/height/layers/milliseconds/error`，`result.cancelled` 为执行取消标记。API 目前同步执行；Eto 面板使用共享服务的后台任务路径，支持响应式取消。完整示例及测试见 [Export-Panel.md](Export-Panel.md)。

## v0.10 真实材质通道

`configure_view` 的图层新增 `{"kind":"texture","textureGrouping":"material"}`；`textureGrouping` 可选 `material`（默认，同一有效 RenderMaterial.Id 合并）或 `object`（每个物件一层，全部置于一个“材质”Group）。`blend`、`opacity`、`enabled` 及复制粘贴保持相同契约。`export_workbench` 按保存配置输出真实颜色贴图与现有 UV，不含光照。旧 `kind:material` 与 `export_psd` / `export_named_views` 继续输出图层颜色。新视图默认阴影 `mul ` 在上、材质贴图在下；旧保存配置保持原样。

例如 `settings:{"width":2048,"height":1280,"layers":[{"kind":"shadow","blend":"mul "},{"kind":"texture","textureGrouping":"object"}]}`。只读导出遇到 SceneFlow UV 失效、图片丢失或不支持的透明/块/面级材质会报错，须在材质阶段先修复。


v0.11 ChatKit 对话、参考图片、xatlas 异步展开和新增 `material_chat_*` / `material_unwrap_*` API：[接入与使用说明](ChatKit-Xatlas.md)。


v0.12 原生渲染网格、管体展开和 `material_uv_renderer`：[接缝 UV 与连续管体](UV-Continuity.md)。

## v0.14 随机去重复

- `material_random_settings`：`assetId`、`settings`；建议带读取时的 `expectedRevision`、`expectedCatalogRevision`。保存外观版本，不修改文档。`settings.mode` 为 `auto/off/object/stochastic/macro/structured`，另有 `seed`、`strength`（0..0.5）、`tiles`（2/4/8）、`rotate`、`columns`、`rows`、`rowOffset`（0..1）。`auto` 解析为保存的 `recommendedMode`。
- `material_random_prepare`：`document`、`assetId`，可选 `objects` 或 `layers`、`preview`。异步返回 `id/status/stage/percent/error`，只准备缓存，不应用材质；无目标默认准备预览。按物件模式按稳定目标 ID 分别生成，预览使用公共变体。
- `material_random_status` / `material_random_cancel`：`jobId`，返回上述任务状态。终态 `completed/failed/cancelled`；取消不应用。
- 已开启随机的 `material_apply` 需先 prepare 完成；交互工具的应用按钮自动执行准备 → 必要 UV → 应用。`material_library` 返回每个材质的随机配置与 AI 建议理由。
- `material_native_preview` 使用已准备的缓存，没有缓存时返回原图球体；UI 明确标注。材质变体的 PSD 合并与有限周期限制见 [Randomization.md](Randomization.md)。

## v0.15 植物

仍通过原厂 Platform `run_python` 调用 `McpApi.Execute`，apiVersion=1。植物生成继续使用 `material_chat_start`：自动判断任务；支持原有 `referenceImages`、`reuseSimilar`。状态新增 `kind:plant`、`plant`（生成入库 ID）、`plantMatches`；`imagePath` 为真实新 PNG，找到已有候选时为空。查询/取消仍是 `material_chat_status/cancel`，不增加第二个聊天执行器。

- `plant_library`：可选 query；返回 directory、assets。资产复用 MaterialAsset 的版本、相对 PNG 与 SHA 元数据，增加 `plant:{scientificName,family,genus,cultivar,sources,evidence,verifiedUtc,estimatedSize,anchorU,anchorV}`。PNG 存 baseColor 槽，植物库与材料库分离。
- `plant_import`：asset、path（绝对透明 PNG）；需要真实科学身份与来源，验证透明度并裁透明边距；高度以米计，宽度按裁切图片比例设置。新 ID，不覆盖。
- `plant_update`：完整 asset 快照，使用既有 revision/catalogRevision 乐观并发规则。放置记录保留当时图片和尺寸，不后台修改已有株。
- `plant_select`：document、assetId；打开原生种植工具并选择植物。
- `plant_place`：document、assetId、points:[[x,y,z]]（文档单位），可选 seed（42）、minScale/maxScale（1）、mirror（true）；返回 objects。原生一次撤销。
- `plant_scatter`：document、assetId、surfaceId，count（20）、spacingMeters（1）、seed（42）、minScale（.85）、maxScale（1.15）、mirror（true）；返回 objects/requested/placed/limited。
- `plant_settings`：无参数读取全局朝向；settings:{mode:auto|z|free,angle:60,transition:5} 保存并重绘。
- `plant_instances`：document；读取可见独立植物锚点的 ID、位置和放置设置，不修改文档。
- `plant_organize`：异步整库 AI 整理，返回 CatalogJob；查询/取消使用既有 `material_catalog_status/cancel`，jobId。科学身份、来源、图片和尺寸不变。

Workbench 图层新增 `{kind:"plants",plantGrouping:"individual"|"species"|"all"}`，默认 species 并置顶；blend/opacity/enabled、配置复制仍支持。视图配置 `plantShadows:true` 控制独立阴影中是否包含植物透空投影。`kind:display/texture/material` 不烘焙植物。规则及限制见 [Planting.md](Planting.md)。

# 原厂 Rhino-MCP-Platform 接入

RhinoSceneFlow v0.5.0 不启动 MCP 服务，不监听额外端口，不修改 Platform 私有实现。使用已安装的 Rhino-MCP-Platform 的 `run_python` 工具，在 Rhino UI 线程调用公开入口：

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
| `export_named_views` | `document`, `directory`, `views:[{viewId,width,height}]` | `channels` 默认 `["material","shadow"]`；`collision` 默认 `number`，也可为 `overwrite`、`cancel` |

所有请求均需要 `apiVersion: 1` 和 `operation`。返回统一为：

```json
{"apiVersion":1,"ok":true,"result":{}}
```

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

默认 `includeFormShading=false` 排除可见面背光产生的本体明暗，保留朝向太阳的面被其它几何遮挡产生的投射阴影（也包括凹面自遮挡）。设为 true 时，背光面也填为同一阴影色。双面网格的法线按相机方向统一；不依赖对象原始法线方向。

接收面必须是模型中实际可见的表面，支持地面、墙、曲面；不自动创建无限地面。隐藏对象不参与投射或接收；透明材质仍视为不透明网格。曲面使用阴影专用细分网格近似，仍非解析 NURBS 阴影。`bias` 可指定正数（模型单位）以控制数值自相交误差，默认 `max(ModelAbsoluteTolerance*0.001,1e-7)`。旧 `ray` 后端还按局部顶点切平面偏差移动光线起点，已确认会越过邻近遮挡面而漏影，不能将该启发式视为可靠修复。

无阴影时仍输出一个完全透明的 `Shadow` 图层，`empty=true`。阴影和色层使用同一相机、画幅及尺寸，保持视图不变时可直接对齐。PSD 内只有独立 `Shadow` 像素层，可在后期调整。

## v0.4 阴影体后端

在 `export_shadow_psd` 请求中加入 `"backend":"volume"`。省略时保持旧版 `"ray"`；未知值返回 `invalid_request`，不回退。结果中的 `backend` 标识实际执行的后端。`describe` 当前返回版本 0.5.0 和该参数。

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

`export_named_views` 每个视图写一个 PSD，选中的材质色层和阴影层组合到同一文件。材质通道当前是图层色，不是纹理或渲染截图。`views` 使用 `named_views` 返回的 id 作为 viewId，宽高均显式给出；按请求画幅调整相机，保持文档主视图不变。

API 不弹覆盖窗口，默认重名编号；显式 `collision:"overwrite"` 才允许覆盖已有原名文件。同一批次的清理后同名视图仍编号避免互相覆盖。`collision:"cancel"` 在遇到已有文件时整体拒绝预检，返回 `ok:false`，不写入文件。所有尺寸、视图、通道先预检；运行中单项失败则记录该项错误并继续其余视图。

`result.files` 含 `viewId/name/path/ok/width/height/layers/milliseconds/error`，`result.cancelled` 为执行取消标记。API 目前同步执行；Eto 面板使用共享服务的后台任务路径，支持响应式取消。完整示例及测试见 [Export-Panel.md](Export-Panel.md)。

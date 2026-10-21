# 原厂 Rhino-MCP-Platform 接入

RhinoSceneFlow v0.2 不启动 MCP 服务，不监听额外端口，不修改 Platform 私有实现。使用已安装的 Rhino-MCP-Platform 的 `run_python` 工具，在 Rhino UI 线程调用公开入口：

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

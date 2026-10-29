# 文档切换与 Worker 边界

2026-10-29 在 B 通道复现 v0.13.1：打开 AI 材质对话后执行原生 `_-New _None`。PID 40352 抛出未处理的 `ObjectDisposedException: MaterialChatView`，栈为 `Panel.Controls → BindableWidget.Unbind → MaterialsTool.Dispose → WorkspaceHost.RefreshDocument → UITimer`，之后管理器记录 ExitCode 3 / AbnormalExit。只有材质库时相同新建操作未复现此异常。证据 `artifacts/rhino-B/document-switch/events-40352.log`。

父布局在解除绑定时仍会遍历其逻辑子控件。先 Dispose 子面板、再 Dispose 父布局会使这一遍历访问已释放控件；仅将外层 Content 设为空不够，DynamicLayout 的逻辑行与视觉层次是两套引用。反过来先 Dispose 布局也不成立：子控件在 Detach 时还需要有效的父控件。第一次修复被回归中的 `tools[materials].error` 检出，未把“未闪退但工具失效”算作通过，证据保存在 `first-fix-failed`。

v0.13.2 在父子都有效时先移除外层内容、清空 DynamicLayout 逻辑行，再释放其拥有的子工具，最后释放外层布局。MaterialChatView 改为真正的 `Dispose(bool)` 重写；先解绑 NativeControlHost 再释放 WebView2。PSD 卡片 / 细节页也按同一所有权顺序处理。注册的系统宿主仍由 Rhino 所有，不在插件退出中自行 Dispose。

关闭文档时只停止文档任务与更新，不在 CloseDocument 事件中重建面板。材质页停止计时器、取消应用 / 对话、停止 ChatKit 后端；异步初始化在每个 await 后检查停止状态。UV 页停止队列；按文档序号取消由 API 启动的 xatlas / tube 任务。PSD 页沿用取消导出与停止预览。工作区等活动文档不再处于打开 / 创建 / 关闭阶段后重新绑定，并记录异常边界到 MCP `tools[page].error`。正常回归必须此字段为空。

## Worker 建议

采用 Rhino 内薄适配层与外部 Worker 的分工，而不是把整个插件或 Eto 面板搬到进程外：

- Rhino 内：命令、Eto / WebView2、当前文档和选择、原生视口 / RDK 捕获、生成几何快照、撤销和最终提交。
- Worker：AI 请求、xatlas 计算，以及后续可拆出的纯阴影计算、图像处理和 PSD 写入。输入是拥有独立内存的数据或临时文件，不是 RhinoDoc / RhinoObject / 面板句柄。
- 任务：由 Rhino 会话、文档、任务 ID 标识；支持取消。返回时检查原文档仍有效、对象与输入版本一致，避免旧结果写入新文件。关闭 Worker 失败不应阻塞 Rhino 文档关闭；Worker 故障也必须明确报告。

当前 AI 和 C++ xatlas 已有独立子进程，tube 与部分 PSD / 阴影使用进程内后台任务。v0.13.2 没有把全部计算移到进程外。后续 v0.13.3 已增加本地库跨进程锁、元数据恢复、版本冲突保护及聊天进程会话隔离，并以多个独立写入进程加 B Rhino 验证，范围见 [Shared-Library.md](Shared-Library.md)。Worker 能隔离部分计算故障，不能替代 Rhino 内的正确控件和文档生命周期。

原厂面板生命周期说明：[Rhino Tabbed Panels](https://developer.rhino3d.com/en/guides/rhinocommon/tabbed-panels/)。

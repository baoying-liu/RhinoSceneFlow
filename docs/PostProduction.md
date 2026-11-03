# AI 后期 Web 工作台 · v0.18.0 第一阶段

**v0.19.0 已接入真实图片修改、单块测试、批量处理、像素约束、融合与完整 PNG 下载。当前用法和限制见 [真实生成说明](PostProduction-Generation.md)。下文保留 v0.18 初始阶段记录。**

运行 `scripts/Setup-PostProduction.ps1` 安装专用 Python 运行环境的依赖。Rhino 命令 **RhinoSceneFlowPostProduction** 打开新增的原生 Tool 并启动浏览器。工作区下拉菜单也有「AI 后期 · Web 工作台」，打开面板本身不自动弹出网页。

本次为开发包/B 通道验证，不生成新的离线分发 ZIP。现有离线分发输入只有旧 ChatKit 依赖；下次发布前必须补齐并验证目标嵌入式 Python 的 PSD/Pillow 及其传递依赖 wheels，打包脚本会拒绝缺失的新依赖，安装探针也检查 PSD 环境。

原生面板列出当前 PSD 导出目录的最近 50 个 PSD，可将所选文件交给网页，也可通过文件选择器读取其他 PSD。网页支持本机路径和文件上传两种导入方式。每次导入创建独立文件快照，不改写源 PSD；源文件复制期间发生变化会拒绝导入。Rhino 交接的当前文档路径/序列号/视图名只表示提交时上下文，不声称匹配旧 PSD 的导出相机。

## 当前能力

- 解析 8-bit RGB PSD / PSB、分组、位置、可见性、透明度、混合模式，原始合成图与图层缩略图。
- 图层用途：可修改、参考、保持原样、排除；修改分组用途同步子项，子项可单独覆盖。用途目前仅记录在计划，不改变原始合成预览。
- 分块最大边长 512/1024/1536/2048；每侧上下文 32/64/128/256；核心边长 = 最大边长 - 2 × 上下文。核心不重叠且完整覆盖画布，边界上下文裁至画布，点击分块查看精确像素坐标。
- GPT 描述助手通过现有本机 Codex ChatGPT 登录执行，只输出 reply/prompt。每次使用近期历史、图层用途及配置快照，可选发送整图预览。未指定/未验证具体 GPT 型号，不冒充 GPT Image 生图调用。
- Shell、Apps、Browser、Computer Use、MCP、子代理、Hooks 和 image_generation 均不向此描述任务开放。只确认描述，不执行生图、改图或导入材质库。建议经「采用这份描述」写入编辑框，再保存配置；运行期间修改配置不覆盖新状态，结果保留旧 revision 标识。
- 项目、对话、配置、任务日志与 JSON 处理方案持久化；任务队列有实际状态和取消。网页刷新可重新跟踪进行中的任务；服务重启保留项目/对话，但不自动恢复中断进程或假报成功。

第一阶段使用 psd-tools + Pillow 完成读取和预览；**NetVips/OpenCV、局部生成、结构漂移检测、融合、结果 PSD 输出尚未接入**，UI/API 均明确标识。处理方案下载为 JSON，绝不是生成完成的 PSD。复杂调整层、智能对象和效果的合成不保证与 Photoshop 相同。

## 进程和数据

新增 HTTP 服务只监听 `127.0.0.1`，使用随机 Bearer、Host/Origin 校验、无跨域授权；不是 MCP 服务。浏览器入口使用 fragment 临时传递凭据，随后清理地址栏并保存在该来源的 sessionStorage。服务日志不记录访问 URL。

数据在 `%LOCALAPPDATA%/RhinoSceneFlow/postproduction`；每项目的 source.psd、document.json、project.json、preview.png、缩略图和 jobs 为该服务所有。PSD 解析在独立 Python 子进程、串行队列运行；不访问 RhinoDoc。Rhino 侧在 UI 线程抓取值数据，后台只发送文件路径和序列化上下文。关闭面板、New/Open、Rhino 退出不结束服务，网页「关闭服务」仅在没有活动任务时正常退出。文件锁阻止多个 Rhino 同时启动重复服务。

第一版限制：单文件 <=2GB；画布/单层每边 <=8192、<=67,108,864 像素；最多 256 层/组、512 个分块。仍可能占用较大内存；独立解析进程不等于系统内存配额隔离。项目不会自动删除。

## Platform 自动化

仍通过原厂 Rhino-MCP-Platform 调用 McpApi：

```json
{"apiVersion":1,"operation":"postproduction_start","document":1,"path":"C:\\Exports\\01 View.psd","browser":false}
{"apiVersion":1,"operation":"postproduction_status","jobId":"LAUNCH-JOB-GUID"}
```

path 可省略，只启动工作台；browser 默认 false。start 不阻塞 Rhino，返回启动任务。status 的 completed 只表示服务启动/文件提交成功；importJob 是后期服务自己的 PSD 解析任务，必须另外轮询它。返回 url 含本机 Bearer，不能打印、提交或放进公开日志。Web HTTP 合同：`/api/status`、`/api/projects`、`/api/import`、`/api/upload`、`/api/projects/{id}/settings|plan|download|chat`、`/api/jobs/{id}` 和 `/cancel`。配置保存需要 revision，陈旧保存返回 409。

验证：`scripts/Test-PostProduction.py --psd <PSD> [--codex <exe> --chat]` 测真实 HTTP/PSD、鉴权、两种导入、源哈希、配置冲突、分块覆盖和重启持久化；--chat 调用真实文本模型并发送演示预览。B 侧 `Test-PostProductionRhino.py` / `Check-PostProductionRhino.py` 通过公共 MCP 验证面板和交接，不使用系统鼠标。

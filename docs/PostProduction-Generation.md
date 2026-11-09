# AI 后期真实生成 · v0.19.0

输出为完整 PNG，不输出结果分层 PSD。原始 PSD 和用户的描述/配置保留，后期助手仍只整理描述；点击明确的生成按钮才使用图片额度。

## 使用

1. 运行 `scripts/Setup-PostProduction.ps1` 安装/更新依赖。命令 `RhinoSceneFlowPostProduction` 打开网页，导入或从 Rhino 提交本机 PSD。
2. 设置图层用途，与描述助手讨论后「采用这份描述」，或直接填写整体描述。
3. 保存分块参数，点击原图上的一个分块，选择「测试选中分块」。先生成整图风格参考，再修改该局部；其他区域保留处理底图。
4. 用「原图 / AI 结果 / 左右对比 / 可修改范围 / 共享风格参考」检查。图块结果窗口显示原始 AI 图块、实际生成尺寸、回填尺寸和轮廓距离；原始 AI 图块尚未恢复只读区域。
5. 「开始整图 AI 处理」处理整幅画面。默认复用兼容的风格/已完成图块；描述、用途或轮廓保护变化会建立新风格，不复用不兼容结果。分块尺寸变化时只复用匹配坐标的图块。
6. 可取消并继续、重试失败/待检查的图块。待检查结果未合入最终图，查看后可「确认此块并合并」。下载完整 PNG；未完成版本和单块测试有明确标识。

## 图层约束

- generate：贡献可修改的可见像素范围。
- reference：用于上下文，自己不贡献编辑范围；其可见 alpha 会遮挡下方图层的贡献，因此参考层不是完全冻结画面的全局开关。
- preserve：恢复其可见贡献覆盖的原始像素，包括半透明边缘；不依靠模型遵守提示词。
- exclude：从该版本的处理底图移除。分组 preserve/exclude 优先于子项；容器 reference 不覆盖子项的独立用途。

从上到下按 alpha/透明度计算保守的可见贡献，额外保留可编辑材质边界周围的 0..3 像素（默认 1）。最终 RGB 在 mask=0 处与该版本底图逐字节相同，alpha 始终与底图相同。原来的植物轮廓及只读内容会恢复，但原始 AI 图块可能改变了它们，故检查图块与最终合成图须区分。

当前实际修改支持 8-bit RGB 的普通像素层、norm/multiply 与普通不透明无蒙版的组；剪贴层、非像素层、其他混合模式、带透明度/蒙版的组会在调用模型前拒绝。导入预览依然允许更复杂 PSD，但不承诺与 Photoshop 的全部效果一致。

## 生成和融合

继续使用本机 Codex 的 ChatGPT 登录，不增加 API Key 计费后端。开启其 image_generation 能力，禁用 shell/apps/browser/computer/MCP/子代理/hooks；只接受本次 thread 的真实新 PNG。此适配器没有承诺指定 GPT Image 2.5 型号、采样 seed 或 API quality 参数，实际可用图片能力由本机 Codex/账号提供。

所有局部共享一张目标风格图，同时提供原整图、局部方形填充图及编辑蒙版。方形画布保留原图坐标，不拉伸输入；模型返回同宽高比结果才能按记录尺寸重采样回填。UI 记录实际生成尺寸与回填尺寸，回填像素数不代表模型原生输出分辨率。

后期 Worker 使用 psd-tools + Pillow/NumPy、libvips 的 Python 绑定 pyvips（与 .NET NetVips 为同一图像内核）以及 OpenCV。大图裁切/PNG 组装由 libvips 完成；重叠低频 RGB 的稳健中位差求有界零均值偏移，再用带 64px halo 的分条多频段融合，最后恢复原始只读像素和 alpha。对齐/轮廓检查仅提示风险，不证明没有窗框、道路、草地等内部细节漂移；尚不支持几何重构任务。

PNG、快照、实际生成收据、单块尝试及融合版本均在项目 runs 内。完成的 tile 不因失败/恢复重复生图；复用的来源有记录。生成取消停止本地自有进程树及后续请求，不保证上游已开始的图片请求退还额度。发布前再次检查取消，临时文件不作为已完成图片提供。服务重启保留结果并把进行中版本标为中断，需手动继续，不自动重复计费请求。

图像处理通过独立进程串行执行，不访问 RhinoDoc。默认最大 8192 边长、2GB PSD、256 层/组、512 块为准入上限，并非 8K 性能或质量保证；当前真实生成验收为 1200×900 演示。Windows 文件读取/原子替换的短暂共享冲突使用有界重试，不截断或删除现存状态文件。

## MCP / HTTP

沿用原厂 Platform。`postproduction_request` 返回一个原生请求任务，用 `postproduction_status` 获取 response；其中生成任务是异步的，再轮询 Web job。仅支持本机工作台的 JSON 路由，下载图片在网页进行。

```json
{"apiVersion":1,"operation":"postproduction_request","route":"/api/projects/PROJECT_ID/generate","method":"POST","body":{"revision":2,"mode":"tile","tileId":1}}
{"apiVersion":1,"operation":"postproduction_request","route":"/api/projects/PROJECT_ID/generate","method":"POST","body":{"revision":2,"mode":"all","styleRunId":"OPTIONAL_PREVIOUS_RUN"}}
{"apiVersion":1,"operation":"postproduction_request","route":"/api/jobs/WEB_JOB_ID"}
{"apiVersion":1,"operation":"postproduction_request","route":"/api/jobs/WEB_JOB_ID/cancel","method":"POST"}
```

HTTP：GET `/api/projects/{id}/runs[/{run}]`；POST `.../generate`、`.../runs/{run}/resume`、`.../runs/{run}/retry/{tile}`、`.../runs/{run}/accept/{tile}`；GET `.../runs/{run}/image/base|mask|style|result|download`、`.../runs/{run}/tile/{tile}`。服务使用现有 Bearer、Host/Origin 检查；含 bearer 的启动 URL 不打印/提交。

## 验证

- `Test-PostProductionRaster.py`：独立合成夹具，排除层、半透明 preserve、alpha、轮廓边缘、分块融合、单块远处不受影响。人工夹具不当作 AI 结果。
- `Test-PostProductionProvenance.py`：新 PNG 的路径/线程/时间、遍历与过期拒绝，Windows 并发读取/原子状态发布。
- `Test-PostProductionImages.py --images --keep`：实际软件流程生图，明确消耗图片额度；不带 --images 仅测试只读预检、取消与恢复，不调用模型。
- `Resume-PostProductionImages.py`：保留真实图片后升级服务，继续融合不重复生图，再将单块风格/像素复用到批量任务。
- `Verify-PostProductionImages.py`：Pillow 独立解码真实 PNG，验证原始只读像素/alpha、新图片收据和前后对比。

本次真实示例完整 PNG 与前后对比在 `artifacts/examples/PostProduction-v019`，证据留在忽略目录。未生成新的离线 ZIP，离线分发须补齐与嵌入式 Python 匹配的全部科学计算/libvips/OpenCV wheels 后另行验证。


### v0.19.1 左右对比

选“左右对比”后，直接拖动图中金色中线（左侧 AI 结果，右侧处理底图），也可使用上方滑块。中线可用 Tab 聚焦，左右箭头每次 1%，Shift 每次 10%，Home/End 到两端；无已合并结果时不显示中线。结果摘要新增复用旧图块/空白跳过/待确认数量。连续强度控制尚未实现：当前采用固定保守结构提示词，Codex 生图未锁定图像模型或传原生 strength 参数，不能把合成 opacity 当作模型重绘强度。

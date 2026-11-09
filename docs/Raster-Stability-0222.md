# 0.22.2 · 底图、局部范围与高清分块

## 修改

### 同一份输入像素

未排除可见图层时，PSD 图层只计算蒙版，不再强制重新合成底图。Studio 将当前导入图作为 canonicalBase，独立项目使用与导入一致的 composite 路径。

确实排除可见图层时才重新合成。前检展示实际底图，成功任务的 inputVersion 固定保存这份底图及 originalAsset；原始节点、过去的比较输入、备份均不改写。

### 明确的修改范围

描述下增加“修改范围”：整图调整／局部修改。整图模式明确提示箭头和文字不构成像素保护。局部模式提供绘制区域入口，要求考虑框内有闭合修改区域；保护区域优先。没有区域时前端阻止生成，后端在模型调用前独立拒绝。

旧文件没有此参数时使用内部 auto 兼容行为，仍理解原有区域和旧式笔画；不会因升级改变旧任务的编辑范围。恢复默认会保留标注，并根据现有区域显示模式。

### 图块、质量检查和融合

- 新计划均衡分配 core，边缘 context 向图内平移。1024 × 768、块 1024、上下文 64 的旧 896/128 尾块变为两个 512 像素 core，均有足够上下文。
- 计划签名包含 rasterVersion 和图块几何，不把旧坐标候选冒充新版结果；已保存运行继续保留自己的冻结坐标。
- OpenCV 前后向一致的特征跟踪检测相对底图位移；相邻已完成候选额外检查重叠区的位移和低频颜色差异。它们是 review 提示，不是几何正确证明。
- 采用 OpenCV MultiBandBlender 与归一化重叠覆盖。测试过 GraphCutSeamFinder，但它与当前分条融合组合产生数值伪影，真实四块重建测试复现后已移除。使用固定输入坐标，不把建筑和地形进行自由变形配准。
- 增加最终融合的颜色数值边界检查及真实纹理四块重建测试，不能只检查单个图块。重新融合可通过原厂 MCP 或检查页面调用，复用已批准图块、保留当前图为备份，不消耗新的生图调用；输入/参数改变或备份满时拒绝执行。
- 修正覆盖权重：完整覆盖区不再用羽化权重第二次混回旧底图；部分试块仍在 core 外平滑退回批准底图，保护像素和 alpha 原样保留。
- 输出尺寸低于输入尺寸时显示降采样提示；检查页面展示结构位移和相邻块诊断。

## 开源参考

沿用已有依赖，没有下载另一套模型或加入 ComfyUI。

- [Real-ESRGAN tile_process](https://github.com/xinntao/Real-ESRGAN/blob/master/realesrgan/utils.py)：参考上下文与有效写回区域分离的设计；没有复制网络或加载它的权重。
- [OpenCV 官方拼接示例](https://github.com/opencv/opencv/blob/4.x/samples/python/stitching_detailed.py)：参考接缝与融合分离的结构；实际试验图割后发现分条数值问题，最终使用已有 OpenCV 的多频段接口与归一化重叠覆盖。
- [psd-tools PSDImage](https://github.com/psd-tools/psd-tools/blob/main/src/psd_tools/api/psd_image.py)：核对 force／layer_filter 与兼容预览的不同合成路径。

## 验证记录

- `scripts/Test-RasterStability.py`：真实 Hillside PSD 的输入与保护像素一致、alpha 一致、排除图层实际输入固定、历史输入不动；闭合局部区域要求；整图/局部语义；多种比例图块精确分区与上下文边界；已知位移诊断；完整覆盖无旧底图重影。候选像素测试是合成夹具，零模型调用。
- 现有 Test-PostProductionRaster、Test-TaskInputs、Test-CanvasContext、Test-BoardWorkflow、Test-BoardInvariants、Test-PostProductionProvenance、真实 HTTP/PSD 与 Boards 回归通过。
- 实际 headless Edge 的局部模式和 raster 前检通过；同样在 B 服务的 Hillside 独立副本中通过。无系统鼠标输入。
- PhotoCraft 真正绘画两次、重新打开、取消及原图像素/历史/单一参考槽保护通过；参考层眼睛、独立 AI 开关、列表/连续模式/画布及导出像素回归通过。
- `scripts/Build.ps1` 与 B 管理部署均成功，0 warnings / 0 errors。B 管理任务 `58ec97197a814379a00a29d99f648426`，原生 PID `112716`，原厂 Platform 22801，部署 `20261109-200841-933782a0f92d4c7e9f761adc3caf912e`。原生及 Web 均为 0.22.2；正式 Rhino 未改动。
- B 新整图真实生成完成：139,451 个保护像素相对导入图零变化，alpha 零变化，实际 receipt 在 `artifacts/rhino-B/raster0222/whole-verified.json`。

真实高清任务与看图结果另见本目录证据的 `hd-progress.json`、`real-case.json` 及后续最终验证文件。自动检查可能漏检，也可能要求检查本可接受的变化；不可把模型漂移描述为已经获得严格几何保证。

## 最终 B 实例与真实成图

最终管理任务 `92edf002f81847509c0b5c849db5ad8a` 成功，PID `93112`，部署 `20261109-202232-3edf639728fa42b89b21cb549f8a023b`；Web PID `102704`。9 个运行代码/静态文件逐字节匹配源码，正式 Rhino 未改动。

共 5 次真实图片调用：1 张整图 + 4 个 1280 × 1280 上下文图块，模型实际返回各 1254 × 1254，再按确定坐标回填为 2048 × 1536。四块无需人工接受，也没有触发重试。特征位移中位数约 0.44–0.68 像素，重叠区诊断通过。

初版图割融合虽然通过了单块检查，最终大图却出现黑线和竖向色带。该失败输出和初步记录保留为 `HD-failed-graphcut.png`、`preliminary-verified.json`；没有将其作为交付结果。增加真实纹理四块一致重建测试后，去掉图割路径，并加入最终颜色数值边界检查。

经原厂 MCP 的新 recompose 路由复用这四张图，完成原节点更新；失败版本成为只读备份，重新融合没有增加图片调用。最终输出数值异常像素为 0，alpha 一致，人工检查未见此前的黑线、竖向色带和明显融合断缝。它仍不是对所有模型输出结构不变的保证。

测试画板：`Hillside 0.22.2 - pixel and tile verification`，ID `2ccdbbd05ebf4b7ca645402e0c63321b`。

- [最终高清 PNG](../artifacts/rhino-B/raster0222/HD-new.png)
- [整图 PNG](../artifacts/rhino-B/raster0222/whole-new.png)
- [最终真实验证记录](../artifacts/rhino-B/raster0222/real-verified.json)
- [真实网页结果](../artifacts/rhino-B/raster0222/final-result-browser.png)
- [图块检查及重新融合入口](../artifacts/rhino-B/raster0222/final-review-browser.png)

`Test-Recompose.py` 验证保留旧结果、相同输入关系、参数改变拒绝、容量满时不启动及失败不发布；实际 B 也核对了失败图片在备份中逐像素一致。局部模式、任务前检、参考层可见性与 PhotoCraft 的回归通过。用户原有偏好恢复，当前选择新测试画板，未使用系统鼠标，未制作新 ZIP。

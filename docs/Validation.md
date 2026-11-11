# v0.2.1 验收清单

## 2026-11-09 · 家里 B 0.22.4 安装核对

管理构建/加载任务 `87027f3741a5461489400878d15fb02b` 成功，0 warnings / 0 errors。原厂 Platform 按本机 B 的监视记录校验 PID116984 / port22801，实际程序集及 Web 服务版本均为 0.22.4；46 个 Web 部署文件与源码哈希一致。原有两份画板的 board.json 哈希保留，文档 Objects=0、Modified=false。实际 headless Edge 渲染“编辑与标注”面板与 0.22.4 页脚，无 JavaScript 页面错误；通过原厂 MCP 打开工作台。此轮为安装及页面冒烟验证，没有重新声称执行所有编辑/生成回归，没有模型调用。证据 `artifacts/rhino-B/home0224`。

## 2026-10-31 v0.16.4 植物来源与实际生成

复现用户失败的两个旧 botany 日志：`a3939124ba7c4354a7db3c812a115f8a` / `65b3c21355a74b68b7d9eb17ef0c392c`（共享库 chat-jobs）。原程序只核对回答中挑出的来源，Kew 403 / PDF 无法读取时直接结束，遗漏搜索到的 NParks。现核实最多 12 个支持域名页面、4 并发、6 MB 上限，记录状态/超时/不支持 PDF/身份不符/重定向。精确科学名+科名仍必须出现在同一真实物种页；标题或显式科学名字段防止相关物种提及误过。

`BotanicalSourceValidation`：来源域名与恶意后缀、403 后备选 HTML、PDF 不按 HTML 处理、物种/科名分散不通过、错物种正文提及不通过、标题 NBSP 规范化、明确科学名字段、非支持重定向与取消；最终 `--plant-only` 通过，日志 `artifacts/botany0164/plant-validation.log`。最初未规范 NBSP 的强化版本失败证据留在 `final-validation.log`；修复后定向检查通过。首版完整 Core 检查在 `artifacts/home0161/botany-validation.log` 通过。

真实 B 安装运行中 HttpClient 核实 Kew 403、NParks 200；插件生成一张全新 Tamarindus indica PNG，随后最终身份验证剔除错误引用，保留 NParks 物种页、UF/IFAS ST618、两棵 NParks Heritage Tamarind 和 IFAS Assessment，原 PNG/SHA 未改动。植物属性保留学名、分类、标签、12 m 表现高度和估计标记。并非用旧图代替生成；输出在本机共享植物库。最终 B PID 33868，部署和退出证据见 Sandbox-B.md。

## 2026-10-30 v0.16.3 ChatKit 本机环境修复

`Setup-ChatKit.ps1` 安装固定依赖、pip check 通过，脚本优先 Windows py launcher。初次安装后仍失败的真实日志：Rhino 导出的 Python 环境让 venv 子进程从 `.rhinocode/py39-rh8/Lib` 导入 argparse/re，触发 `SRE module mismatch`。ChatKit 以 `-I -X utf8` 启动，不修改 Rhino 自身变量。`Test-ChatKitProtocol.py` 故意设置不兼容 PYTHONHOME/PYTHONPATH，真实 SDK 的 SSE、上传、图片事件、持久化、token 轮换与鉴权仍通过（fixture agent，不调用模型）；`artifacts/home0161/chatkit-isolation.log`。

沙盒管理构建/安装任务 `b4a04c30c50a4f47b705013d216c1f00` 成功；B PID 90640 内原生 WebView2 ExecuteScriptAsync 读取组件 ready=true、error=null，插件 chatKit=ready。恢复用户未保存模型副本，保留原路径文件；当前 AI 页已打开。未为本次 Python 启动修复重跑无关的几何/PSD 全套回归，也未实际生成一张新的材质图。详见 Sandbox-B.md 和 `chatkit-restored.json`。

## 2026-10-30 v0.16.2 山地演示与持久化 UV

家里 B 实际生成三种材质和一份经植物资料核实的 Betula nigra PNG，并通过插件的随机贴图准备、真实尺寸 UV、上材质、种植及工作台 PSD 完成演示。69 个非植物对象、15 株（4 手工）、3 Named Views；最终 PSD 1200×900、11 像素图层、底到顶 Arctic / 材质 / Shadow / 植物，10736 ms，独立 psd-tools 解码透明度与结构通过，不是 Photoshop UI 验收。

第一次旧版重开真实发现 32 个 Brep 箱式 UV 无效；几何 CRC 未变，原生映射网格二进制归档变化。保留 `Hillside-Retreat/reopen-uv-review.json`。改为数值顶点、面、UV、法线和映射变换的语义指纹，备份仍用原生完整归档；保留仍匹配的旧哈希兼容分支，已失效记录正常重算。B 数值独立构造等价映射指纹相同，改 UV 或 UVW 变换指纹不同；`scripts/Test-MappingFingerprint.py`。

最终 v0.16.2 完整 Build.ps1、实际保存/重开、69 个 UV valid、15/4 种植恢复、五页 error=null、Modified=false 及重新导出通过。`artifacts/examples/Hillside-Retreat/reopened.json` / `verified.json`；当前 PID 69292，最终任务 `61fee537e4a54a21b54b6282098fadbd`。PID 78340 / 24568 NormalExit。立即重开后种植短暂 busy 是稳定等待，未将其提前认定完成。第一次兼容代码的枚举命名空间编译错误已修正，最终构建日志通过。模型并非施工图；玻璃是示意不透明色板，等高线不动态更新，素材移机须重新关联，见 [演示说明](HillsideDemo.md)。

## 2026-10-30 v0.16.1 植物卡片／双语名称

`plant0161-release.log` 完整构建、原有检查及打包通过。新增 `PlantNamesValidation` 验证中文／英文显示、缺名时科学名回退、外观 revision／图片 SHA／科学身份／默认株距不变、catalog revision 增长、旧快照拒绝及已有名称保护。新生成的植物带中英文显示名；旧库实际通过同一本地 Codex 元数据任务完成名称补全，不生成图片。发布仍使用既有共享库锁与事务恢复。

真实 B：三个测试植物经 Eto DragDrop 事件加入计算列表，首次间距来自对应资产。手动改为 6 m 后切换中文卡片、英文列表、英文卡片，三项保留且手调值不被默认值覆盖，学名逐 ID 完全一致。`Test-PlantShelfUi.py` / `Check-PlantShelfUi.py`、`plants0161/ui-verified.json`；这是原生控件事件测试，没有模拟鼠标拖动。实际 WPF 420 DIP 截图检查了缩略图、两行名称、三列紧凑布局、独立模式选择及固定底栏。图片缓存有 64 张／160 px 上限，此次没有将小样例检查描述为千素材压力测试。

新建文件时发生原厂 MCP 端点重置，重连 PID 不变；五页 error=null，语言与图标偏好保留，原库恢复，`new-verified.json`。NormalExit／重启后重新打开原种植示例，12 株／2 手工及 4 m 组合参数保留，文档 Modified=false；`ready.json`，截图 `ready.png`。PID 61576、13784 均实际 NormalExit/code0／空 CrashEvents 和 Dumps，最终 PID 12568，部署与实例见 Sandbox-B.md。既有 PID 65412 退出证据不足继续保留为 UnknownExit。

## 2026-10-30 v0.16 参数化种植

最终部署 `20261030-180754-24f790b068db4aefbc229f6e77680cb8`，任务 `474db12c65c34839b0082156abfb8f4a` 成功，B PID 65412 / Platform 22801。最终完整检查及包日志 `plant016-release-final.log`。重开示例恢复 12 株／2 手工、五页健康、只读 PSD；`ready.json`。四组同时提交后均完成，平移和两倍缩放数值正确，临时组清理；`bounded-verified.json`。实际 SDK 闭合盒体在显式焊接前后裸边均为 0；`closed-boundary-sdk.json`，不把它记作已复现的旧接缝缺陷。最终选中截图确认青／橙两种真实轮廓；`selection-colors.json`。

最终 SDK 同路径 WriteFile 曾报“file could not be opened”，没有删除锁文件或强行覆盖；改另存唯一示例名成功，当前 `SceneFlow-Planting-Composition-65412.3dm`。没有足够证据将该失败归因于插件或确定为文件锁。后续对当前示例实际修改对象属性并执行原生 `_Save`，同路径覆盖成功且 Modified=false，`native-save-verified.json`；这是另一次真实标准保存测试，不改写此前 SDK 失败。独立解码最终三份 PSD 仍通过（12 / 1 / 1 层，species/all 差 0）。

标准验证／打包 `artifacts/plant016-release.log` 全通过。新增 `PlantLayoutValidation`：面积密度（含坡面）、手工总数、混合半和间距、权重、三个独立随机流、零密度保留手工、边缘大小、突破间距、JSON 值快照和取消。边界距离采用裸边包围树，避免候选逐条扫描；布局 Worker 最多两个。真实 AI 仅重新核实物种／间距，没有生成第二张图片：Acer rubrum 成熟自然冠幅用途建议 15 m，实际页面学名／科名验证成功；`plants016/spacing-ai.json`。原真实资产的建议间距／依据更新，PNG 未改；示例组合显式按 4 m 选择用于演示，不冒充成熟株距。

B 原生第一轮 PID 15628：单个网格根保存 60 株、其中手工 2 株。size/mirror 参数改变不动布局；网格改为坡面后所有基部及重心附着跟随，面积目标变 61，撤销恢复 60。原生命令一次提交两点，手工变 4，重算总数仍 60。删除面保留 60 株并提示重新关联，撤销恢复；`plants016/phases.json`。Brep 手工 UV 附着在承载面平移 3 m 后跟随；`surface-tests.json`。

第一轮复制回位失败被保留；局部 SDK 实验证明 UserData 在 Add 之前赋 Transform 会重置为单位变换，修正为先 Add 再 Set。第二轮 PID 17672 原生复制平移 25 m 后稳定，实际保存／New／Open 后非单位变换仍在，五页 error=null、Modified=false；`final-verified.json`、`reopen-verified.json`。Eto 原生 DragDrop 事件及两个 Slider ValueChanged 无鼠标提交，组合第三项和 .8 / 1.6 参数落盘；`ui-input-verified.json`，没有把事件测试描述为实际鼠标拖动测试。选中组时库折叠，420 DIP 布局与固定操作底栏检查见最终 `Planting-v016/panel.png`。

最终示例（PID 45320 创建）：地形与一个种植根，共 12 株、手工 2 株。改变为远处不同拓扑后保留两株手工且 detached=2，撤销恢复；`topology-detached.json`。1000×700 PSD 独立 psd-tools 解码：单株 12 个像素层、按种 1 层、全部 1 层，植物组置顶，species/all 最大预乘 RGBA 差 0；`psd-verified.json`，不是 Photoshop UI 验证。导出耗时约 1668 / 1029 / 621 ms。示例与 PNG 预览位于 `artifacts/examples/Planting-v016`，3dm 仍引用本地库图片。

测试中保留脚本断言纠正：ObjectTable.Count 包含已删除记录，删除检查改为 FindId==null；新 Named View 加入后显式刷新已打开的 PSD 面板再配置；PIL 只读数组改为副本。均未作为插件崩溃。之前 PID 16092 的旧实例有 rhino-closing 标记但缺退出码，按 UnknownExit 留档并确认，未认定 NormalExit；`previous-exit-review.json`。本轮 PID 15628、17672 均通过管理器真实 NormalExit；任务 `19a05f95f1bb4a04a0cf630bc74fb9dd`、`23524e8b9b684541bf4260b3c112190b`。最终部署／重开见 Sandbox-B.md。

## 2026-10-30 v0.15 植物（补齐最终原生预览）

最终重开 B：PID 16092，任务 `4a1b8686c8874390bd547699de774eae`，部署 `20261030-134551-01c7fbe15e5945e3917176be47cda4a9`。同一代码重新准备组合后成功加载；原模型四株植物、库路径与五工具页恢复且 Modified=false，`native-cutout-restart-ready.json`。原生覆盖启发式首次约 97.02%，重启约 96.99%（不是逐像素渲染契约）；原定恰好 97% 的临时阈值过于贴近此 LOD 边界，改为允许 5% 的预览差异，PSD 完整 Alpha 与独立源图 oracle 不放宽。启动器初始化耗时另留 `launcher-restart-stack.txt`，采样为 UI 定时器枚举历史任务／路径检查；没有修改启动器。

`Build.ps1` 全部通过：`artifacts/plant-release-final.log`。标准验证新增植物科名／学名来源边界、Z/free/auto 朝向、预乘 Alpha 边缘、非植物裁切、单株保留、交错种类／全部合并一致、嵌套科学名称 PSD、Alpha 透空投影、128 MiB 分块拒绝、非居中镜像锚点和共面俯视地面。后两项先出现可复现失败，再修复通过。

真实 B 通过原 `material_chat_start` 实际搜索植物资料并生成新 PNG：Acer rubrum，Sapindaceae / Acer，裁切后 1109×1363；`ai-verified.json`。进一步实际 HTTP 页面核实学名与科名、参考图片输入和库内真实候选缩略图复用通过，不产生第二张图片；`visual-reuse-verified.json`。AI 整理三项库后验证图片、尺寸、科学身份、来源、外观版本不变；`jobs-status.json`。

B 的 13 株合成 Alpha 夹具、8 株带最小间距散布和真实植物混合场景，三种输出独立 psd-tools 解码：单株 14 层 / 学名 2 层 / 全部 1 层，植物组置顶；species 与 all 最大误差 2。独立 Python 相机射线／原 PNG oracle 500 点最大误差 2，增加植物投影 742 像素、最大 Alpha 增量 255；`final-psd-verified.json`、`oracle-verified.json`。不是 Photoshop UI 验证。

同一官方 ChatKit 元素通过 `sendUserMessage` 实际提交植物对话，原 UI 切换植物按钮并隐藏材质范围；`chat-ui-verified.json`。实际 ChatKit 启动生成后原生 New，任务 cancelled、未导入新素材、工具切到新文档且 error=null；`document-verified.json`。New/Open 的一次 HTTP 10054 是端点重置，重连 PID/文档检查通过。仅 Rhino 打开的工具页会实例化；最终健康检查逐页激活后要求全部五页，修正了测试脚本把未实例化页误判为失败的断言。

原生透明曾经过经典材质、PBR Alpha、透明图、深度写入和显式 Blend 原型，PBR 单株改善但俯视重叠仍出现矩形缺口；这些原型图片保留为失败证据。最终实现改为缓存 Alpha 轮廓网格、8 档透明度、延伸 RGB，源码 `PlantPreviewGeometry.cs`。10 月 30 日资源恢复后，同一请求成功安装；实际透视与俯视重叠预览检查通过，未再出现矩形缺口，墙体遮挡正常。原生着色像素覆盖 PSD 不透明植物内部约 97.02% / 99.02%，保留轮廓 LOD、光照和透明度分档差异，不将此统计称为逐像素相等。独立 psd-tools 解码确认植物组置顶、透视 53873 / 俯视 90699 非零植物像素；`native-cutout-verified.json`。两张 1000×700 PSD 导出约 1966 / 721 ms，文档 Modified 保持，五工具页全部 error=null。CPU PSD 独立于原生显示路径，地面共面修正证据仍为 `known-top-before.psd` 对照 `delivery-psd-verified.json`。

多个已测试进程真实 NormalExit/code0：46884、15648、61948、57912、13876。管理 MCP 的一次 close 返回泛化错误，但持久任务与 `plant-close-status.json` 证明 NormalExit，不把传输错误当崩溃。最后关闭任务 `71dec6c74e194ec4beb921effef215fe` 成功。未杀 Rhino、未修改其他通道、未使用鼠标。系统提交内存先 94.3% 后约 97.5%，高于管理器 94% 准入，`start_job` 未提交；`plant-native-memory-block.json`。只关闭自己的 B 和编译服务器，没有调宽策略或关闭用户应用。

唯一真实样例已加入原本地植物库（不加入合成夹具），资产 `e55d4f7b-0f15-49e9-bddf-dd999c2d79b7`；原材质库根路径恢复。示例 PNG、四株树／墙／地面 3dm、1000×700 透视／俯视 PSD 在 `artifacts/examples/Planting-v015`；`published-asset.json`、`delivery.json`。所有证据在 `artifacts/rhino-B/plants015`。最终部署 `20261030-133859-afa56b19dafb49cd8fea7666a3bd0730`，任务 `14e2f38546a74e949a544b8d5fbef98e`，PID 51448。关闭初次 CloseTimedOut 被实际可访问窗口确认为 Rhino Update Available 提示；其后真实退出记录为 NormalExit/code0、CrashEvents/NewDumps 均为空，见 `native-cutout-exit.json`。保留超时任务，不把进程消失等同正常退出；没有强制结束进程或安装 Rhino 更新。

## 2026-10-29 v0.14 随机材质

最终部署 PID 68604：原生缓存球体渲染、420×950 侧栏展开区换行和所有五页健康检查通过；`ready.json`、`native-sphere-final.png`、`random-ui-final.png`。准备随机贴图期间执行原生 New：HTTP 一次 10054 重置，重连确认同一 PID、新文档、任务 cancelled、五页绑定新文档且 error=null；`new-verified.json`。无需操作鼠标或终止 Rhino。

PID 68604 随后真实关闭为 NormalExit / code0，crashEvents 与 newDumps 均为空：`artifacts/random-final-close.json`。测试后的重启使用同一已构建部署，不额外生成 AI 图片。

四种随机方式的确定性、正负 UV 周期、原图像素密度、结构边界、线性颜色、法线单位长度及高度有限差分方向 oracle 已加入标准验证。`Build.ps1` 全部通过，日志 `artifacts/random-release-final.log`。真实外部 TextureWorker 由 Pillow/Numpy 独立解码，四种方式、不同分辨率 PBR、SHA、缓存复用与重复相关性通过，证据 `artifacts/random-worker/verified.json`。

B PID 62356 实际 Eto 应用两个物件：独立随机变体、自动准备 UV、随机平铺 4 倍覆盖并保留密度、原生材质 UVW 及缓存尺寸通过。独立 PSD 解码验证默认材质合并 1 层与按物件 2 层合成相同；两个场景各 3042 个内部像素与实际原生贴图采样 oracle 最大误差 0。见 `artifacts/rhino-B/random014/{object-export,stochastic-export,psd-verified}.json`；不是 Photoshop UI 验证。

实际生产对话生成新混凝土 PNG 后，AI 自动建议 stochastic；独立实际砖墙图片识别建议 structured、禁止旋转并返回网格。取消准备未改变物件，通过真实 Eto Apply 自动保存 macro/2/seed88 草稿，两个物件实际使用 256×256 缓存。证据 `ai-status.json`、`ui-verified.json`。曾因测试脚本用 materials 页 MCP 按钮去触发 library 页未保存草稿而断言失败；改用实际 library 页按钮后通过，不将错误测试视为产品故障。测试结束恢复原材质库，保存唯一测试模型。

早期 GDI 长路径写入、OneDrive 临时目录发布争用与沙盒全局 OutputPath 的 worker 拷贝问题均已复现并修复。保留 `random-job*.json` 和相关日志。开始时旧 PID 16780 已消失，manager 判为 UnknownExit / code0，没有 crash event 或新 dump；不能称为正常退出或确定崩溃。此次 PID 62356 的真实关闭为 NormalExit / code0、无 dump，保存在 `artifacts/random-before-final.json`。方法与限制见 [Randomization.md](Randomization.md)。

## v0.13.3 本地共享库并发（2026-10-29）

Release 零警告 / 错误，完整 Core 验证通过，包含新增真实多进程并发验证，日志 `artifacts/shared-library-release.log`。4 个写入进程并发导入 32 个资产、80 次外观和 80 次标签修改，精确核对 revision=81 / catalogRevision=161 / 宽度累加；两个读者和整库整理并发，无部分分类快照；旧版本保存拒绝；实际终止自有持锁 / 部分写入测试进程后自动恢复。最新回执 `artifacts/validation/library-concurrency-617e5783519d47808c6dc63d46751d1d/verified.json`。初始压力运行发现同步目录短暂 rename access-denied，加入有界重试后完整验证通过，未退化成原地覆盖。

B 部署 `20261029-144514-21ef13a3d30d44fba018469418b49c8e`，任务 `acc2d2c4abae47f5a6079b9be30f7669` Succeeded，PID 58892 / Platform 22801。真实 PNG 私有测试库与两个外部写入进程 PID 18476 / 59996 共同运行：17 个资产自动进入列表，草稿保留，旧标签 UI / 旧资产 API / 旧尺寸 UI 保存拒绝，重新选择可保存，外部整库整理后分类不被旧尺寸界面覆盖。新建文档仍访问相同 17 个资产；恢复原 B 库，4 个原资产保留。ChatKit 文件按进程会话 / 文档 / 面板隔离。

证据 `artifacts/rhino-B/shared-library0133/verified.json`、`external-writers.json`、`cross-document.json`、`ready.json`。PID 58892 最终 NormalExit；重启任务 `8e1a75d35ecc4334b230319160cac24d` Succeeded，当前 PID 16780 / Platform 22801，实例 `6641ca74df6f4ab0a79e3529bea523df`，重开后原库路径、4 个资产、工具健康状态和新会话路径通过。没有启动第二个 Rhino 实例；没有正式部署或操作鼠标。保护范围见 [Shared-Library.md](Shared-Library.md)。

## v0.13.2 AI 工具文档切换（2026-10-29）

在 B PID 40352 实际复现 AI 对话打开后新建的未处理 `ObjectDisposedException: MaterialChatView`，栈指向父布局 Unbind 访问已 Dispose 子面板。管理器记录 ExitCode 3 / AbnormalExit。此前 PID 25552 同样 ExitCode 3，但没有其调用栈，不推定两者必然同根因。失败记录 / 退出确认保留；`events-40352.log` 为直接复现证据。第一次修复未闪退但暴露已释放 DynamicLayout 父节点错误，因 `tools[materials].error` 非空判定失败并修正，证据 `first-fix-failed`。

最终构建日志 `artifacts/doc-switch-build.log` 零警告 / 错误、完整 Core 验证通过。B 部署 `20261029-141022-f253a7a8fd254d919d1cc07807628878`，任务 `0b206d577fdb487aaaeffccaa741cdbe` Succeeded，PID 63680 / Platform 22801：

- `Test-DocumentLifecycle.py`：全部工具打开，AI 页保持可见，3 次原生 New 与 3 次原生 Open 交替，PID 一致、文档序号变化、全部工具绑定新文档且 error 为 null。证据 `document-switch/verified.json` 与 after-*.json。
- `Start-/Check-DocumentWorkCancel.py`：实际 xatlas Worker 启动后立即 New，任务 cancelled，新文档为空，旧结果没有回写，所有工具正确重新绑定。证据 `cancel-verified.json`。
- `Test-/Check-ChatStartupClose.py`：New 后立即建立 AI 页，在 ChatKit 尚未 ready 时再次 New，两次切换成功，无工具错误。证据 `startup-close-verified.json`。
- `Test-/Check-ExportDocumentClose.py`：创建真实 Named View 卡片并打开相机 / 太阳细节后 New，全部工具重建成功。证据 `export-close-verified.json`。
- 独立材质库同步、A→B 实时应用、自动 UV、列表高度复测通过，证据 `library0131/verified.json`（PID 63680）。无鼠标操作、没有请求新 AI 图片。

总计最终进程内 10 次文档替换。之后管理器确认 PID 63680 NormalExit；重启任务 `0f3605b61e6042c7aeec924e26abcd10` Succeeded，当前实例 `71f73e9881d14981b8f9ec22a7879e77`，PID 56356 / Platform 22801。`Ready-DocumentLifecycle.py` 检查重开后的 v0.13.2、五工具与当前文档绑定及空错误字段，证据 `document-switch/ready.json`。进程内后台任务与外部 Worker 的边界及本次范围见 [Document-Lifecycle.md](Document-Lifecycle.md)；未宣称已实现多个 Rhino 实例并发写材质库。

## v0.13.1 独立材质库（2026-10-29）

Release 零警告 / 错误，全套 Core 验证通过（`artifacts/library-split-build.log`）。B 任务 `572c9b6f51a8454db5442efbaac32c11` 成功，PID 51908 / Platform 22801。`Test-/Check-/Finish-LibraryTool.py` 实测五个注册面板、AI 独有 ChatKit / 库独有 MaterialShelf、双向材质和应用范围同步、从独立库对实时选择 A→B 应用、自动米制 UV、第一次目标保持不变。证据 `artifacts/rhino-B/library0131/setup.json`、`first.json`、`verified.json`。

首次布局捕获发现库列表被其他内容挤压为零高度；修正为滚动库内容和固定应用区。最终部署 `20261029-133829-e5608356616644c5b78c06fcbe99c25f` 由任务 `ae2bce4dd4d94e068b188bc62192be63` 成功加载，PID 25448 实测同一套独立库 / 实时选择 / UV 流程通过，列表实际高度 230 DIP，截图确认列表可见且应用按钮固定。证据 `setup.json` / `first.json` / `verified.json` / `library.png` 已更新；初版证据保存在 `before-scroll`。重启任务 `5c913ff66244402e845cc03cf67d8c1f` 成功，PID 25448 被管理器确认为 NormalExit，重开 PID 25552 / Platform 22801，`Ready-LibraryTool.py` 验证版本、五面板和无 ChatKit 的独立库通过（`ready.json`）。

历史更新任务 `f0e6297285a3492ba7f8aae07be022ca` 因旧实例关闭超时失败；保留原进程和备份，未强制结束或补开实例。Mini dump `close-51908.dmp` / `close-stack.txt` 确认主线程阻塞在 `Toolbars.ToolbarsPlugIn.AskAndInstallUpdates → Notification.ShowModal → Dialog.ShowModal`。Computer Use 重试 / 重置后仍无 native pipe，未输入鼠标或键盘。用户手动关闭更新提示后，管理器最终将 PID 51908 记为 NormalExit；原超时证据保留，不将其改写为成功任务。

## v0.13 工作区验收（2026-10-28）

最终安装 PID 44696 / 22801（任务 `c75f0220677448cd9f8f9df98badbc96`）。实际重开自有模型后验证选择状态与材质库同步、错误文档 ID 拒绝；窄页 / 824 宽并排库自动切换和不相似红铜描述返回零匹配通过。最终两视图工作台实际操作 2K 预设、尺寸复制、图层深复制和细节页返回，两个独立预览均加载；批量生成两份 PSD 并独立解码。证据 ready / layout-verified / batch-ui-verified / export-verified / decoded.json。

最终模型另存为 `SceneFlow-Workspace013-ready-abd18a35.3dm`。对打开的旧 fixture 原路径保存曾出现原生只读文件锁对话框，导致 MCP 查询等待；Live dump / cdb 栈确认 `CRhLockFile.DisplayReadOnlyMessage → RhinoDoc.WriteFile`，不是 PSD 写入或 UI 卡死。通过 computer-use 只读窗口状态，没有鼠标输入；改存新路径后 MCP、保存和解码均通过。测试保存脚本已改用新唯一文件名，未删除锁或覆盖原文件。原厂 Open 命令的 HTTP reset 仍按 PID / 文档重查处理。

- Release 零警告 / 错误与全套 Core 回归通过，新增分类筛选交集、完整 ID 集、去重词汇、图片 / 尺寸 / 外观版本不变、元数据过期拒绝测试。最新完整日志 `artifacts/ui013-delivery-validation.log`。
- B PID 49928 实测四个原生 Eto 标签同一 dockBar；材质 / UV / 种植占位 / PSD 导航、库展开、连续三次选择、原生 RDK 球体预览、实时选择 A→B 与自动补算米制 UV，通过原厂 Platform API / WebView2 SDK 完成，没有鼠标输入。
- 实际 ChatKit 发送石灰岩请求，Codex 返回两个可信已有候选，未生成新图；关闭复用后仅请求一次真实新图，生成深蓝陶瓷 PNG，自动命名 / 归类 / 六个标签、导入、选择与应用成功。独立 SHA256 / PNG 解码通过。
- 实际点击 AI 整理，三个资产的三类（天然石头、石材、陶瓷）统一为石材 / 陶瓷；全部图片哈希、尺寸、PBR 参数、外观 revision、文档材质绑定、几何 CRC 不变，仅 catalogRevision 增加。分类 / 标签筛选和空选择拒绝通过。
- 新侧栏工作台实际启动异步 320×240 PSD 导出，包含真实石材与新生成陶瓷、独立阴影（正片叠底 75%）、极地模式。psd-tools 独立解码与强制合成通过，材质组 3 个子层、蓝色材质 2529 个可见像素、阴影 alpha 非空。导出保留文档修改标记、数量、相机、太阳状态。没有使用 Photoshop UI 验证。
- 主要证据在 `artifacts/rhino-B/workspace013/`：setup / reuse-verified / generation-verified / organize-verified / export-verified / decoded.json；可查看样例 `artifacts/examples/Workspace013/SceneFlow-Workspace.psd` 与 PNG。WPF 截图不含 WebView2 的 HWND 内容；材质球和 PSD 使用独立原生 / 文件验证。

本轮开发失败记录保留：早期 RDK 预览前使用独立 viewport 的 DrawToBitmap 返回 null，已改用实际 RDK 缩略图接口。一次本地分类测试在 OneDrive staging 文件夹改名被拒绝，测试改为独立临时目录后通过；另有预览 Color4f 编译错误任务失败，未部署该版本。

B PID 58024 在管理器关闭时超时，随后异常退出（0xC000041D），不是通过。已保存原模型恢复备份和退出 / dump 分析证据；`ui013-shutdown-dump.log` 定位 `ObjectDisposedException → Eto.Panel.Controls → Native TabPanel OnUnLoad / DataContext`。修复注册面板生命周期：Rhino 保有宿主所有权，插件关闭只停止任务、先脱离内容再释放；文档关闭不释放仍挂在宿主上的 ExportPanel。修复后 PID 49928、4344 均由管理器记录 NormalExit / code 0；不据此宣称更早历史的所有崩溃原因均已解决。

## 自动验证

- [x] .NET Release 编译通过，无警告。
- [x] 多颜色几何共用深度缓冲，前景遮挡后景。
- [x] 非共面场景反转三角形绘制顺序，像素归属保持一致。
- [x] 近裁切面穿越、侧面越界及完全位于近面背后的三角形。
- [x] 透视投影近远边界与视锥边界。
- [x] 透明背景与完全遮挡颜色组不生成图层。
- [x] 相邻色块抗锯齿后图层合成与参考像素一致（量化容差内）。
- [x] 取消写入保留原文件。
- [x] 独立 psd-tools 1.26.0 解码、Unicode 名称与图层重新合成检查；预乘 RGBA 最大差异 1.486/255。

## Rhino 沙盒 B 实机验收

- [x] Rhino 8 .NET 8 模式加载 v0.2 RHP，通过原厂 Platform API 和命令导出；不使用鼠标。
- [x] 红蓝 Mesh 面遮挡场景，俯视与透视导出；核心投影与 Rhino WorldToClient 误差小于 0.01 像素。
- [x] 两个同 RGB 图层合并，独立 PSD 解码确认图层名称与像素颜色。
- [x] 验证隐藏对象、父图层隐藏、锁定对象。
- [ ] 块实例及嵌套变换实机验证。
- [x] 球体、双曲抛物面、单叶双曲面、圆环及裁剪孔洞，平行和透视导出；原生 CurveBrep 参考采样检查通过。
- [ ] SubD 与大坐标模型实机验证。
- [x] 验证输出后文档 Modified、对象数量、图层属性、相机、显示模式、选择保持原状态。
- [ ] Photoshop 打开文件，不出现修复提示；确认中文名、透明背景、分层与合成画面。
- [x] 简单场景 512 px，复杂曲面 1024 / 2048 px 的导出与分层检查。
- [ ] 大场景内存、窄缝和共面对象专项检查。
- [ ] 在布局及裁剪视图中返回明确的不支持提示。
- [x] 默认目录持久设置与自动命名；MCP 导出不弹保存窗口；命令回车使用默认路径。
- [x] API 已有文件保护、非法宽度、错误视图、错误版本和不存在文档均返回失败。

真实文件已通过独立 psd-tools 解析与重新合成；Photoshop 应用本身尚未打开验证。完整记录见 [B 通道报告](Sandbox-B.md)。

v0.2.1 修复马鞍曲面被默认网格退化为单四边形的问题，见 [复杂曲面报告](Complex-Surfaces.md)。

## v0.3.0 独立阴影增量验证

B 通道 PID 78996 的最终版本通过独立阴影验收：3,689 个原始 Brep/NURBS 参考采样、单色与透明边缘、墙面和曲面接收、背光面开关、Rhino Sun、样式参数、原生命令及默认 2048 像素输出。阴影样例 334,028 三角形，默认导出 1,736 ms。色层复杂形体回归仍通过。

修复了平滑曲面背光分界的三角碎纹；完整方法、失败证据与限制见 [Shadows.md](Shadows.md)。本次通过外部 psd-tools 解码及预览检查，未打开 Photoshop，未发布到正式 Rhino。

## 2026-10-22 准确性复核：已确认漏影

v0.3 的切平面法线偏移在接触反例中会越过遮挡片，导致应为 alpha=255 的阴影变成 0。旧版采样通过不构成完整准确性保证；太阳角度测试也补上了 BeginChange/EndChange 和实际角度断言。详情、对照及替代方案见 [Shadow-Alternatives.md](Shadow-Alternatives.md)。当前后端尚未修复该漏影，不应将研究验证完成解释为后端精度通过。

## 2026-10-22 v0.4 阴影体增量

新增独立命令 `RhinoSceneFlowExportShadowVolumePSD` 和 MCP `backend:"volume"`。仅通过固定 B 通道部署，管理任务 `16674f059d1745cabbb734352b91fd2d` 成功加载 PID 26432，部署 `20261022-153951-18aa2cfcb65b41eda600206989d8e536`。未发布正式 Rhino，未使用鼠标。

`Build.ps1` 核心检查通过；真实 PSD 的 1,564 个原始 Brep 参考采样无不一致，近接漏影反例的新后端中心 alpha=255（旧后端仍为 0）。默认 2048×1047 导出约 9.1 秒。独立 psd-tools 验证单色、alpha、重合成及真实命令，未打开 Photoshop。实际 135°/45° Rhino Sun 的自动和显式方向 PSD 字节一致，完整渲染设置恢复。

同一网格的射线参考与阴影体透视结果仅 2 个像素相差 64 alpha；曲面分界仍有细碎纹理，不能将采样通过解释为全部像素或解析曲面精度保证。旧后端漏影未修复。详见 [Shadow-Volumes.md](Shadow-Volumes.md)，证据在 `artifacts/rhino-B/volumes/`。

## 2026-10-22 v0.4.1 原始曲面复核

阴影体后端自动复核曲面不确定采样和覆盖边界两侧，修正已复现的双曲面碎影。含明暗边界的独立解析参考检查 9,049 个像素、36,196 个子采样，0 不一致；另 2 个混合接收面轮廓像素通过。原始 1,564 个稳定区参考、近接漏影反例、样式、太阳、实际命令、默认输出和独立 PSD 解码重新通过。

最终 B 构建 PID 267632 的 PSD 与已验证结果字节一致。此场景默认 2048 输出约 34.1 秒，未做 GPU/C++ 迁移；未进入复核区的几何仍有网格近似限制，不能宣称任意模型精度保证。方法、前后放大对比与复核命令见 [Shadow-Accuracy.md](Shadow-Accuracy.md)。

## 2026-10-22 v0.5 Eto 面板与批量 PSD

`RhinoSceneFlowPanel` 在 B 的 PID 249608 实测。Named View 的 320×200、384×192、240×240 输出均通过；按视图独立尺寸、重名 002/003、显式覆盖、取消预检、材质/阴影单通道及合并通道、三种原生预览模式和尺寸刷新保留通过。7 个 PSD 独立解码和重合成，最大预乘 RGBA 差约 1.97/255；不同通道组合中的材质和阴影图层分别逐像素一致。

实际后台导出 352×224 成功，运行期间 UI 定时器响应 66 次；通过真正的 Eto 取消按钮取消 2048 输出，无 PSD 或临时文件残留。文档主视图、尺寸、图层及选择状态保持。没有操作鼠标或 Photoshop。完整复核脚本、报告路径与限制见 [Export-Panel.md](Export-Panel.md)。

## 2026-10-22 v0.5.1 直射阴影和预览窗口修复

本地 Build.ps1 完整构建和几何/投影/PSD 回归通过。Rhino B 的完整太阳直射阴影新增两个方向 8,552 像素独立参考检查，全部通过；纯投射阴影双曲面密集边界共 9,011 像素及两个混合接收面像素通过。两个真实近接反例的阴影中心均为 alpha=255。

当前场景同条件 1024×587、包含背光面及自身遮挡，旧完整计算 168,719 ms，新版 15,864 ms；601,088 像素 alpha 完全一致。旧版默认纯投射阴影与此基准不同，不能混为同一速度对照。后台面板 352×224 输出为 2,721 ms，UI 定时器在运行中继续触发；实际取消按钮取消 2048 输出后无 PSD 或临时文件残留。

方法、范围及证据见 [Shadow-Direct.md](Shadow-Direct.md)。所有运行仅在 B，PSD 通过独立解析器解码，没有打开 Photoshop、接管鼠标或部署正式 Rhino。

最终 UI 构建 PID 68104：七个真实批量 PSD 检查通过，最大重合成差约 1.77/255，各种通道组合中的材质及阴影层一致。Shaded/Rendered/Arctic 图片预览通过，实测预览 545×347。三次开关面板前后保持同四个视图、没有浮动视图，相机/尺寸/模式/视图名/选择/Modified 保持，测试结束面板关闭。证据：`panel/verified.json`、`panel/windows-verified.json`。

## 2026-10-23 v0.6 多视图工作台

本地 Build.ps1 构建与核心回归通过。新增 6 种混合公式、RGB 像素、文件夹混合 / 透明度、磁盘暂存、裁剪窗口和大尺寸写入验证；8192×2048 核心 RGB PSD（134,217,888 字节）经独立解码及首尾采样检查。

B 的 PID 227176 完成真实 Eto 多卡片、添加 / 删除空图层、启用空项拒绝、1K/2K/4K/8K 预设、独立复制粘贴及深复制、细节相机与太阳、关闭重开恢复和两张配置各异的 PSD 导出。psd-tools 验证实际图层顺序、材质分组、RGB 显示模式、混合 key 与透明度，独立重新合成最大预乘 RGBA 差约 1.906/255。旋转 / 缩放后的原生着色前景和独立材质轮廓 IoU 约 0.9703（原生边线和抗锯齿使其不是逐像素一致）。主视图、显示模式、太阳、对象、选择、视图列表及 Modified 保持。

1200×720 分块与原整张输出相比，接缝两侧带状区域逐像素一致，alpha 全图一致；全图有 1 个非接缝像素的 RGB 差 30/255，保留为曲面边界子采样数值差异，**不是全图字节一致**。检验脚本限制此类差异最多 4 像素、最大 64/255，另对接缝和 alpha 使用独立更严限制。证据保留在 `workbench/report.json`、`verified.json`，不对任意几何宣称解析精度保证。

B PID 265612：临时 Named View 写回通过，方向变化约 0.2478 弧度、数量和太阳恢复；真实两视图按钮后台导出成功，UI 定时器在忙碌时响应 89 次。真实取消按钮取消 4096×2048 请求，结果 cancelled=true、无 PSD / tmp 残留，状态保持。Eto 布局图显示两列卡片与分别可见的预览，无需接管鼠标。

实际工作台 8192×2048 材质通道导出 7,889 ms，6 个材质像素图层、89,075,902 字节，全部图层和合成图独立解码通过。该测试证明超过旧 800 万像素上限的工作台路径，不代表完整 8192×8192、多显示模式或阴影均已在此尺寸验收。

测试早期的 PID 205400、274748、227176 出现未能确定原因的实例退出，没有可归因的应用错误事件 / 转储；管理器保留 UnknownExit、Successful=false，未将退出记为通过。后续实例单独完成写回、异步、取消和 8K 验证。未打开 Photoshop，未修改其他通道或发布正式 Rhino。说明与复核脚本见 [Workbench.md](Workbench.md)。

补充：PID 265612 连续开关面板三次，文档视图保持、浮动视图为零；随后管理器关闭请求未收到完整握手，退出仍保留 UnknownExit。最终仅修改滚轮步进幅度，重新构建零警告 / 错误和全部核心回归通过，加载 B PID 175732。合成 +120/-120 Eto 滚轮事件分别产生 1.1 倍 / 恢复原缩放；四张卡片均加载、零浮动视图、256×160 阴影 / 材质 PSD 导出与文档状态保持通过。最终 PSD 再次独立解码，证据 `workbench/final-verified.json`。

家用电脑的独立 B 通道安装、.NET 10 兼容修正、真实分层 PSD / 后台导出 / 取消 / 8K 材质输出结果，以及关闭稳定性限制，见 [Home-B-Validation.md](Home-B-Validation.md)。

## 2026-10-26 公司 B 更新复核

同步 `c4e161b` 后重新构建和全部核心回归通过。更新部署 `20261026-134519-79366444417f4ae9ba5bff01b89e1781` 在公司 B 的 PID 108352 加载成功。4 张卡片预览、滚轮事件和 256×160 阴影 / 材质组合 PSD 通过，零浮动视图、文档状态保持；独立解析图层分组 / 阴影层及合成图，最大重新合成差约 1.773/255。记录保存在 `artifacts/rhino-B/office-update-20261026.json`。此次为安装后的短时验证，不替代之前完整测试，也不宣称退出稳定性问题已解决。
# 2026-10-26 v0.7 材质库验证

最终构建由沙盒 B 的 `build_test` 任务 `cce650d2025042a682a587340470158b` 完成，状态 Succeeded；包含 Build.ps1 核心回归，编译零警告。实际 Rhino PID 116016、原厂 Platform 22801，插件版本 0.7.0。

- `Test-MaterialLibrary.py` 最终证据：`artifacts/rhino-B/materials/run-0481b982/report.json`。原生 PBR 四通道、Normal 识别、平面重复 (1,1)、矩形箱式三个方向、圆柱弧长 / 高度、旋转、毫米 / 米 / 英尺 / 英寸、图层继承与新增对象同步、缩放后重映射、旧 RDK 材质 / 映射恢复、原 Mesh UV 保留、ZIP 跨库导入、真实 Eto 按钮及生成任务回填均通过；测试后原有 live object IDs 保持。
- 交替模拟两种材质的贴图隔离通过；显式 Rendered 图像 `materials/demo/rendered.png` 人工查看，石材地面与棋盘格物件正确区分。材质 Eto 内容截图 `materials/demo/panel-white.png` 人工查看，1110×900 无水平裁切。
- 原生 Undo 在命令退出后的 UI timer 执行，`materials/demo/undo-verified.json` 为 undo=true、fixtureExists=true、bindingRemoved=true。重现顺序：通过 Rhino-Mcp.py 分别运行 Test-MaterialUndoStart.py、Test-MaterialUndoApply.py、Test-MaterialUndoQueue.py；timer 回调后再运行 Check-MaterialUndo.py。这些脚本依赖已准备的自有 demo，期间不能插入其他模型编辑。
- `Test-MaterialExport.py` 导出 320×200 Named View PSD，保留相机、显示尺寸、太阳、Modified 及工作台原配置。`artifacts/verify-env/Scripts/python.exe scripts/Verify-MaterialExport.py` 独立解码通过：自上而下 Rendered / Shadow / 材质图层组，重组与内嵌预览最大误差 1/255。证据 `materials/demo/export-report.json`、`export-verified.json`；未通过 Photoshop UI 打开验收。
- 使用内置 imagegen 真实生成 1×1 m 浅灰石灰岩颜色图，完成 Agent 回填和入库；源图 SHA-256 为 `99253F390405434F3519C50CE1C99368885DCF1B20E1D1521E9C7AA6B26469FE`。完整提示词与源图保存在 `artifacts/materials/source/`。

保留了早期失败证据：BasicMaterial 丢 PBR、TextureMapping JSON 无法还原、RenderMaterial=null 抛异常、同名贴图串图以及旧 UI 布局裁切。最终实现分别使用 FromMaterial、显式 MappingSnapshot、材质索引恢复、资产唯一文件名与独立布局行修复。没有把这些失败版本记为通过。旧 v0.6 测试实例曾 UnknownExit；原记录仍保留，不能据此宣称旧退出问题已修复。

当前范围及限制见 [Materials.md](Materials.md)：AI 需 Agent 实际处理；物理尺寸需标定；变形后手动重映射；不包含复杂自由曲面无畸变展开、块实例映射或自动云服务。
# 2026-10-26 v0.8 米制 UV 与简洁窗口

Build.ps1 核心回归通过，编译零警告 / 错误。B 最终使用部署 `20261026-210109-7bc0cdfa2e96465482ea80502974a8b9`，实际加载任务 `b500a553d5f64083b5353de89eafc2cb` Succeeded，Rhino PID 26764、Platform 22801。

- `Test-WorldUv.py`：`artifacts/rhino-B/worlduv/2a21a042/report.json` complete=true、liveIdsRestored=true。独立计算保留材质、1 米 UV 增量 (1,1)、600×300 mm 贴图原生模拟重复 (1.6666667,3.3333333)、换材质复用同一记录、手动改映射 / 同边界内部网格编辑 / 缩放 / 单位改变的失效识别、恢复无 UV 原状、混合图层有效 / 无效 / 缺失对象、参考图复制及 running 状态均通过。
- 调整后的 `Test-MaterialLibrary.py`：`materials/run-019a5ab7/report.json` 全部通过，保留 PBR 四通道、平面 / 矩形箱式 / 圆柱、英制换算、图层继承、恢复和贴图隔离回归。它现在把米制 UV 与材质物理尺寸组合检查，不再将原始 UV 当作图片重复次数。
- `Test-MaterialQuickUi.py` / `Check-MaterialQuickUi.py` 实际 Eto 操作通过：`worlduv/quick-ui-verified.json`，图层中计算 1 个、复用 1 个，显示 1/2、2/2 和最终 100，两个对象均 ByLayer。取消首步前不修改 UV；生成任务复制参考图片、显示 Agent 阶段、完成回填后自动选中新资产，证据 `worlduv/quick-generation.json`。回填测试复用先前生成的真实图片，不称为新一轮模型生成。
- 首轮原生 Undo 四阶段通过；同时断言 WorldUv 记录随应用撤销。证据 `materials/demo/undo-verified.json` 与 `worlduv/quick-generation.json`。逐物件 UI 流程是多个撤销记录，非整个批次一次撤销。
- `Test-MaterialExport.py` 及独立 `Verify-MaterialExport.py` 再次通过，320×200 PSD 重组最大差 1/255；未打开 Photoshop。Rendered 示例人工查看，石材和矩形棋盘重复正确；580×740 的生成页 / 铺贴页文件截图人工查看，无裁切，应用范围在底部。文件 `worlduv/quick-generation-white.png`、`quick-mapping-white.png`。

保留迭代失败：初版 FromMaterial 丢贴图 UVW，已通过对子纹理 SetRepeat 修复；首次变换测试错误地使用复制模式 False，断言失败并遗留一个自有副本，随后仅按该测试唯一标记清理，改用替换模式 True 后重跑通过。

部署任务 `c8afe7b7d41e43cfa950749515779078` 曾 CloseTimedOut。通过 computer-use 技能检查到 Rhino 退出阶段隐藏的 Update Available 对话框；选择 No 后进程退出，未强杀、未安装更新。保留失败任务及关闭证据，待退出后重新提交 test 才实际加载成功；没有把超时任务标为通过。

撤销复测限制：随后同一实例的重复 SDK / timer 撤销返回 false，等待 recording inactive 和改用脚本命令均未解决。失败证据 worlduv/undo-retry-failure.json，不能认定是定时器竞争，也不能把首轮通过扩展为重复撤销全部通过。保留 Check-MaterialUndo.py 的 WorldUv 移除断言；未修改产品原生撤销机制。显式恢复按钮及材质 / 映射还原测试通过。
# 2026-10-27 v0.9 软件内生成与当前选择修复

最终沙盒 B 部署：`20261027-184155-039d831265654c26a3e66ba84c83977b`，任务 `18c79b8b12a04b568a5a8c96f5374fca` Succeeded，实例 `ebc9d2917aff4beb8a71b5934b2dbca9`，PID 60896，Platform 22801。Build.ps1 编译零警告 / 错误，原有核心回归及新增 Codex 新图片结果校验通过。

- 当前选择：`Test-LiveMaterialSelection.py` → `Check-LiveMaterialSelection.py` → `Finish-LiveMaterialSelection.py`，证据 `artifacts/rhino-B/materials-v09/selection-verified.json`。同一面板从 A 改选 B 后只修改 B；无选择拒绝且无旧对象回退；图层应用按点击时当前对象的图层计算；点击后再改选择不重定向已运行队列。只清理测试唯一标记的对象与图层。
- 实际自动生成：`Test-CodexMaterialButton.py` / `Check-CodexMaterialButton.py` 调用真实 Eto 生成处理器，传入一张混凝土参考图片。最终任务 `e071ed37-d6fe-4098-8d5a-d512e7e7a9f5` 自动启动本机 codex-cli 0.164.0-alpha.11.1，以 ChatGPT 登录生成新 PNG，再由插件自行校验、入库并选中新资产。**没有调用人工 complete 回填**。Codex thread `01a17ead-53a3-78b0-8e9e-9f951f88715e`，资产 `3a0a8f48-9813-4c12-af0b-270bd3ebe26c`。输出 SHA-256 `fa8acfe275afaabcf47102d4ac5814381778c389a161111f19656810f4384e5e`，与参考图片的 `94f4eb73c02ddbef23297a02b504d2b80f7ce2c9bda02fb1a7e76f2c597c458c` 不同。证据 `materials-v09/generation-verified.json` 与对应库请求目录 runner/events.jsonl、generation-prompt.txt。
- 关闭并重新打开简洁面板时，同一实际生成任务继续显示，同时目标切换到新选中的圆柱，证据 `materials-v09/reopen-verified.json`。
- 失败与取消：`Test-CodexMaterialFailure.py` / `Check-CodexMaterialFailure.py` 只为一次请求将进程内执行路径临时指向非 Codex exe，并立即恢复。任务进入 failed，面板显示登录检查失败，按钮恢复可重试；随后启动正常重试并在首阶段取消，进入 cancelled，没有导入图片。证据 `materials-v09/failure-verified.json`。未修改用户认证文件或机器环境变量。
- 原有功能：最终 PID 上 `Test-WorldUv.py`（worlduv/a5a57e3a/report.json）、`Test-MaterialLibrary.py`（materials/run-dafac5a0/report.json）均 complete=true，恢复原 live objects / selection。完整材质库中的实际应用按钮仍覆盖；手动 Agent 交接回归改为明确调用 request API，避免测试误启动真实图片任务。
- PSD 联动与独立解析再次通过，320×200，Rendered / Shadow / 材质组，最大重组差 1/255；文件 `materials/demo/export-5003362c/Materials_Perspective.psd`。未以独立解析代替 Photoshop UI 验收。

本次未修复历史重复 Undo 自动化不稳定问题，原记录保留。中间旧 PID 59516 被管理端记为 UnknownExit，已检查 ExitCode=0、无 CrashEvents / NewDumps 并保留 `artifacts/codex-ui-prior-exit.json` 后确认退出，再重试加载；未强杀 Rhino，未改其他通道。首轮实际生成 PID 42296 也成功完成后正常经管理端切换至最终构建，首轮与最终请求均保留于材质库。

# 2026-10-27 v0.10 材质贴图分层

本地 `scripts/Build.ps1`：零警告、零错误，既有验证及新增 TextureValidation 通过。新增独立世界射线 / 三角形重心 UV oracle、正负重复 / Clamp / V 方向、近侧裁剪、遮挡、按实际材质 / 按物件合成一致、每层独立 RGBA、1030 像素跨 1024 tile 边界以及取消验证。PSD 内每层保留自己的 RGB，不借用整幅合成图。

首轮 B PID 70328 完成平面、箱体、圆柱、球体和对象 / 图层材质继承；两视图各导出合并 / 拆分。6 物件同材质合并成 2 层，同名但 ID 不同的材质保持独立；按物件为 6 层且直接位于单一“材质”Group。两种分层的合成 RGBA 逐字节相同，太阳变化不影响底色；独立 psd-tools 重合成的最大预乘 RGBA 差异为 1/255（Core 交错遮挡夹具约 1.82/255）。真实 Eto 复制粘贴保留分层方式并深复制；失效 UV 只读拒绝。该轮仍有 PBR 默认灰色重复相乘造成的偏暗，不能作为颜色正确的验收；后续独立物理像素 oracle 发现并修正此问题。证据：`artifacts/texture-native-run2.json`、`artifacts/texture-verified-run2.json`。独立文件解码不等于 Photoshop 界面验收。

部署更换时保留失败结果：旧 PID 60896 UnknownExit（code 0）；PID 70328、68588 AbnormalExit（code 3）。均未发现新的 CrashEvents / Dumps；这些结果没有计作测试成功，也没有足够证据归因于某个模块。原始记录：`artifacts/texture-exit-evidence.json`、`texture-exit2-evidence.json`、`texture-exit3-evidence.json`；失败任务 `5393d822c0364f548a8cc35b65b7cf79`、`97b878058d8542bf8a1793750242e54c`、`6e092d218bf34d0081f14ce9b0111dd1`。已审阅并通过管理器确认后重新测试，未强制结束 Rhino；关闭稳定性仍未验收。

本版只支持不透明颜色位图 / 实体颜色，不含光照、粗糙度 / 法线照明、反射、透明裁片、块实例、Brep 面级多材质或程序纹理烘焙。真实 UV 缺失 / 失效和图片丢失必须先修复。并未重做 AI 生成或消耗图片额度。


## v0.11 ChatKit / xatlas 实机验证（2026-10-27）

`Build.ps1` 零警告 / 零错误；原有验证及新增原生 xatlas、真实尺度面积、源面对应、23,040 面三叶结、76,800 面毫米浮点网格、局部重切和取消验证通过。后者故意模拟文档浮点坐标，95 分位拉伸 1.1304、最大 1.9978。`Test-ChatKitProtocol.py` 用明确的 fixture agent 验证真实 SDK SSE、参考图上传、生成图事件、SQLite 持久化、端口 / token 轮换及鉴权；该协议测试不调用模型。真实 Codex 文本调用另经 `--chat-smoke` 通过。

最终办公室 B：PID **78296**、Platform **22801**，任务 `9e9c822a08f94c7580b151c647d3bbba` 成功，部署 `20261027-221139-9a8160dde1a04d5d8307f2195e6d4db6`。76,800 面三叶结 + NURBS 球体网格化 16,128 面，共 **92,928 面，26.112 秒**；原网格 / Brep 类型和 geometry DataCRC 不变。三叶结 465 岛，95 分位拉伸 **1.11477**，最大 **1.99669**，重切 16 面（原最大 107.274）；球体 7 岛，95 分位 1.10142，最大 1.18837，不需重切。总 UV 面积与三维面积一致。这是面积校准，有接缝和局部变形，不能宣称逐点等尺。

真实 ChatKit WebView2 组件 ready / error=null；文本讨论完成且不产生图片；通过组件 `setComposerValue(files)` 上传参考图，再用 `sendUserMessage` 请求生成，两个 response.start/end 成对完成。新 PNG 自动验证、入库、选中，实际资产 `0adc969a-9be0-4a09-9dcc-05b19cc7afac`。Native WebView2 截图见 `artifacts/rhino-B/xatlas/chatkit-ui.png`，回复与图片实际可见；关闭重开后 `setThreadId` 恢复会话和图片。源码中的 stdio 桥使用单行紧凑 JSON，修复首轮“图片已入库但聊天仍停在启动”的问题；首轮失败记录保留在 baseline 中。

材质应用复用 xatlas 记录；3dm 读回的自定义映射网格、纹理坐标和 mapping hash 保留；计算期间替换源几何会拒绝提交，取消不留下 UV 记录。实际 Rendered / Arctic 显示后校准记录仍有效。全程用 Platform、SDK、文件检查，未使用鼠标；仅将 B 测试窗口显示出来初始化 GPU 视图。隐藏的新建 Rhino 在初始化前的原生截图曾只显示平涂 / 线框，不能作为材质可视验证；显示 B 后的真实 Rendered 截图为 `native-unselected.png`，最终 PSD 已重新导出。

完整样例：`artifacts/examples/ChatKit-Xatlas/AI_Complex_Merged.psd` 与 `AI_Complex_ByObject.psd`，含真实 AI 材质、独立 Shadow（正片叠底 75%）和 Arctic。前者材质 Group 一个子层，后者两个直接物件子层。强制独立 psd-tools 重合成两种分层差异 **0**，与存储预览最大预乘 RGBA 差 **1.867/255**；不是打开 Photoshop 界面验收。证据：`artifacts/rhino-B/xatlas/{verified,workflow-verified,guards-verified,persistence-verified}.json`、`artifacts/examples/ChatKit-Xatlas/decoded.json`。

部署期间保留 WebView2 多架构 DLL 冲突、旧 PID 61196 UnknownExit（code 0、无 CrashEvents / NewDumps）、主动取消的中间任务；没有把这些计为通过，也未强制结束 Rhino。WebView2 现仅部署 x64 loader；任务 05 为收拢最终修正主动取消，任务 06 才是最终成功验收。


## 2026-10-28 砖纹与朝向复查：v0.11 尚不能视为原生 UV 完整验收

用户用砖纹暴露了随机混凝土未充分检出的缺陷。办公室 B PID 78296，源对象 `ff19aeaf-aace-4dfa-ae66-d27056ffe7f4`：38400 顶点 / 76800 面，闭合但 SolidOrientation=-1，有向体积 -132889894146.61641 文档单位³；custom mapping primitive 同样为 -1。原因是测试三叶结生成器的绕序朝内，不是 xatlas 把原源几何翻转。已修正生成脚本的绕序并增加正体积 / 外向断言。在未修改活动文档的独立副本中显式反向面索引，验证 orientation=+1、正体积。`Mesh.Flip` 后本次 SDK 的 SolidOrientation 查询仍返回旧值，因此证明使用重建网格与体积两项，不能只读可能缓存的标志。

第二个已确认的接入缺陷：原始共享顶点网格经 native `SetTextureCoordinates(customMeshMapping, Identity, false, true)` 后，23633/76800 面的 UV 边梯度与 atlas 原面 UV 不一致，最大差 30.4118 UV 单位。诊断副本先 `Unweld(0,true)` 再映射，76800 面的梯度误差全部为 0（顶点变为 230400）。该实验同时改变了每面顶点及法线，证明原生回映射不能忠实保持当前分岛 UV，不表示逐面硬法线是正式解决方案。Rhino SDK XML 对 seamCheck 的描述明确只覆盖 Box / Sphere / Cylinder，不包括 custom mesh mapping。

正式修复仍需直接保留分岛 UV 的渲染网格 / 正确的 UV seam 顶点，并保留原平滑法线；不能只靠 custom mesh projector 回套共享顶点原网格。Mesh 和 Brep 必须分别验证原生显示、PSD、保存重开与恢复。砖纹还要求方向 / 相位连续；现有 465 岛 + 异常面再切缝只约束局部尺度，没有约束跨岛图案连续。管状结构可采用沿中心线的连续展开和隐蔽接缝，通用曲面需方向引导分区；不承诺双曲率表面全局无缝且逐点等距。

本轮仅诊断、修正后续 fixture 生成器并保存几何诊断副本；未替换用户当前物件 / 材质，也未宣称插件运行时已修好。证据在 `artifacts/rhino-B/uv-orientation/{diagnosis,outward-verified,native-seam-transfer}.json`。此前面积 / 拉伸 / PSD 检查仍是那些具体检查的通过记录，不构成砖纹连续性或原生回映射正确的证据。


## v0.12 连续管体与原生 UV 修复验收（2026-10-28）

办公室 B，最终任务 `66d93f90374a428da0df53aafd58251b` 成功；部署 `20261028-151756-6ecc52b29a834dfc84d2c06fc3de60ed`；实例 `47abcdb63065428687fc43d77752e42e`，PID 66776，Platform 22801。完整串行 Build.ps1 零警告 / 零错误，原有检查、xatlas 及新增 TubeValidation 通过。一次与管理端重叠的本地构建遇到 CS0006 中间文件竞争，保留失败日志，随后串行重跑通过；未将该失败记为通过。旧 PID 78296 UnknownExit（code 0，无新事件 / 转储）已审阅并确认，不归因于本次修复。

新 RenderMeshProvider 使用接缝拓扑 / UV 与平滑法线，不再把图集重新投影到共享顶点源网格。辅助存储避开已有通道，通道 1 为 surface parameters。原生管线检查：两件 Mesh 与一件 NURBS 球体返回的 UV / 法线误差均 0，闭合渲染网格体积为正；源 geometry CRC 不变。三叶结原源仍朝内，修正只发生在渲染快照中；原几何保留。

76,800 面管体沿中心线展开 4.2282591 秒，长度 86.478382 m、半径 0.699998 m；1 岛，95 分位拉伸 1.178998、最大 1.364121；UV 面积与源面积差约 0.0445%。原生砖纹和 PSD 材质通道均实际检查；有闭合收口、内外弯局部拉伸，不是通用无缝等距参数化。自动 xatlas 测试仍 1197 岛、最大拉伸约 2.0076，不应选作管状砖纹连续性方案。

取消、计算中修改中心线、改动辅助映射 hash 拒绝、恢复、保留无关 1000 通道（本插件使用 1001）通过。六次材质切换保留原 UV，原生 provider 的实际材质重复分别正确为 1/0.6、1/0.3 和 1、1。退休缓存在等待后回到 0，未持续累积。实际保存并重开自己的 3dm 后文档 serial 268435458，三个对象原生 UV / 法线误差仍 0，源 CRC 未变，读取后 modified=false。第一次 Open 因未设置保存选项进入保存提示，取消宏被当作测试文件名，保留诊断；正确设置 UpdateDocumentPath / SuppressDialogBoxes 并确认 modified=false 后 Open 成功。重开期间 HTTP 一次断开，PID 未退出，重连后继续通过，未强制结束 Rhino。

1600×1200 的 atlas / tube 各导出真实材质、Rendered、Shadow+材质+Arctic 六份 PSD，并由 psd-tools 强制独立合成 / 图层解析。预览含采样、色调、光照差异，不宣称逐像素同色；SDK 返回 UV 与法线才作数值一致性检查。证据：`artifacts/rhino-B/uv-v012/{ready,export-verified,guards-verified,reopen-verified}.json`、`artifacts/examples/UV-v012/decoded.json`；原生截图 `tube-rendered.png`，示例 `tube-stack.psd`。仅 B 部署，正式 Rhino 未改。详情见 UV-Continuity.md。
## 2026-10-30 家里安装检查 v0.16.1

完整 `scripts/Build.ps1` 通过，包含原生 xatlas、种植布局、双语名称及跨进程材质库验证。B 安装任务 `0c2b6bc79b4b48d18374e3f961f4a249` 成功；PID 78340 经原厂 MCP 检查版本 0.16.1、五工具页无重建错误、文档未修改。保留 `artifacts/home0161/build.log` 与 `artifacts/rhino-B/home0161/ready.json`。首次编译因固定 VS 2022 generator 与本机 VS 18 工具链不匹配失败，改为匹配已安装 VS 主版本并刷新本地 CMake 缓存后通过；未安装系统工具或改变资源策略。本次为本机安装/打开检查，不代表重新执行所有公司场景回归。

## 2026-11-02 office B update to v0.16.4

Source 022c61f matched origin/master after fetch. Previous office deployment was 20261030-192503-3be88f99e1ad42eea68ece644f4094ca. Build.ps1 completed all core validation and packaging; sandbox build_test job 1f0607a149f843d4b87abf44e2c0fc54 succeeded with zero build warnings/errors. Deployment: 20261102-145406-3f8defee7d7e4893a8ddba2a390bb773; PID 59900, original Platform port 22801. Public describe returned 0.16.4; all five workspace tools opened with error=null. Dedicated ChatKit runtime imports passed under -I -X utf8. No image generation, full UI browser acceptance or PSD export was repeated in this update check. Only fixed office B was updated; no formal Rhino or other channel changes, no mouse use. Evidence: artifacts/office-20261102-build.log, artifacts/office-20261102-status.json and artifacts/rhino-B/office-20261102-ready.json. Instance remains hidden under the existing silent-test setting.

## 2026-11-02 v0.17 Plants List and selection properties

Only office B 1cee488700ad42f59492743cc4a2a3fe was updated through management MCP 19540. Final build_test job bd3dc33d89f643a89d935a10723cef11 succeeded (zero warnings/errors); deployment 20261102-171012-a2e2c1383ee542ccb10861d53d93fd98, PID 59052, Platform 22801, RHP SHA256 64D3FBB2BE411A7868766BF73A328F3E361902EE9FC5ABC30B7D0FEC4DE6FB3F. Public describe returned 0.17.0. Build.ps1 full validation/package completed: artifacts/v017-build-accepted.log. No formal Rhino, other channel, user material library content or mouse input was changed. The managed B window was shown for WPF Loaded/layout inspection, not through simulated input.

Verified: genuine Eto selection/deselection events and native viewport selection in both directions; rename/layer/hidden/locked attributes; hidden/locked group enumeration and lock restoration after hide/show; same-material edits, object isolation and repeat reuse, layer isolation; custom plant type/position/scale/mirror, unchanged density count, exclusion of original automatic instance, persistence across all seeds and carrier deformation, real 3dm Save/Open; custom reset and legacy loose-plant compatibility. Actual properties controls prepared valid world UV before applying PBR changes. Rhino native _Undo/_Redo round-trip passed using ContentUndoHelper (undo.json). New/Open kept PID 59052 and rebuilt all seven tools with error=null; final document is empty, Modified=false, original library preference restored. B remains visible with the properties tool open.

PSD individual/species/all exports at 320x240 succeeded and were independently decoded with psd-tools: 36/6/5 pixel layers respectively, plants above shadow and layer-color passes. Species/all independent composite maximum channel difference was 2/255 (group quantization); not Photoshop UI acceptance. These are synthetic alpha regression plants in an isolated library, not newly AI-generated botanical imagery. Evidence: artifacts/rhino-B/properties017/{setup,selection,verified,psd-verified,undo,ui,reset,ready,workspace-final}.json; PSD-*; plantsList.png and properties.png are WPF layout captures and exclude the native viewport.

Preserved intermediate build errors, failed script assertions, source logs and HTTP resets. Initial direct RhinoDoc.Undo/Redo probes left an active scripted undo/redo record; the isolated fixture finishes its prior scripted record and tests actual native commands after Platform returns. Initial custom snapshot implementation was replaced with Rhino's documented ContentUndoHelper. Open/New HTTP resets alone were not treated as crashes or passes; reconnected PID/document/tool checks supplied the evidence. Raw pointer mouse double-click gestures and interactive GetPoint movement were implemented but not simulated; single-plant API edits and alpha-pick math share the same stored group data. No promise of single-plant Gumball support in this version.

## 2026-11-02 office Hillside reproduction

Rebuilt the home Hillside example through the existing SceneFlow workflow on office B only: PID 59052, plugin 0.17.0, Platform 22801. Real new Betula nigra PNG and three textures generated/classified through the plugin; 69 geometry objects received calibrated UV/materials; 15 trees in group 73fb8208-d869-4935-bb7e-23a6e81e4641 include four manual plants. Actual 1200x900 PSD export: 11 pixel layers, 11039 ms, independent psd-tools decoding confirmed Arctic/material/Shadow/plants. Native Save/Open validation retained the PID, all 69 UV records valid, 15/4 plants, three Named Views, all seven tool errors null and Modified=false. Model is %LOCALAPPDATA%/RhinoSceneFlow/Demos/HillsideRetreat/SceneFlow-Hillside-Retreat-Office.3dm. Original OneDrive-path saves failed and were preserved; local-path native overwrite/reopen passed, root cause unconfirmed. No formal Rhino or mouse input. See docs/HillsideDemo.md and artifacts/examples/Hillside-Retreat/office-reopened.json for complete paths, asset IDs and evidence.

## 2026-11-02 v0.17.1 isolated plant editing

Office B only (management MCP 19540, original Platform 22801). Final build_test job 9a9f6d0b5c514d0a8f08ab1d3285ac09 succeeded, deployment 20261102-183026-a1e4552329744b6ea0175569c53ba445, PID 24484. Build.ps1 full validation/package passed with zero warnings/errors (artifacts/plant-edit0171-accepted-build.log). No formal Rhino, other channel, mouse input or shared library content changes.

Actual Eto GridView CellDoubleClick entered isolation. All 70 normal document objects (including the group root) became unselectable; single-member move kept the other 14 rows identical, copy raised the count from 15 to 16 with no new Rhino object, and cancel restored exact parameter JSON, rows and modes. Real conduit PickGumball found translate and scale handles, ScaleMode XYZ. The actual registered SDK OnMouseDoubleClick override selected an alpha-visible plant and enabled its handle after Platform completion. Native _Undo/_Redo during isolation and _Undo after exit restored exact parameters without stranded locks. Saving during editing finished the session; native Open retained all saved member poses; native New while editing cleared session/Gumball state and kept the PID and tool health. Evidence: artifacts/rhino-B/plant-edit0171/{isolation,callbacks,gumball,undo,saved,reopened,new,ready}.json. No OS pointer gestures or interactive GetTransform.Get drag were simulated; tests exercise native event handlers, native handle picking and the shared transform commit path.

Retained failed evidence: PID 69264 StackOverflowException dump and plant-edit0171-crash-stack.log identify record-generated Vec3.PrintMembers -> Unit -> ToString recursion from SyncHandle. Explicit scalar formatting fixes both the handle stamp and Vec3 diagnostics (zero-vector regression included). Locked-root derived Replace initially failed; the native GeometryBase/ignoreModes overload now updates it without unlocking. Native attribute Undo alone failed after derived mesh replacement; PlantParameterUndo snapshots and end-of-replay restoration passed the final native regression. Earlier Platform undo-scope and handle-timer harness failures remain separate files. The manager correctly refused relaunch until the crash evidence was reviewed/acknowledged; failed jobs remain failed.

Before testing, the dirty user model was copied to %LOCALAPPDATA%/RhinoSceneFlow/Demos/HillsideRetreat/Backups/Before-PlantEdit-20261102-125921.3dm. Final ready model is SceneFlow-Hillside-Retreat-PlantEdit-Fixed.3dm in that HillsideRetreat directory: original 15-tree layout restored, all Named View export settings copied, Modified=false. Original Office.3dm and backup are preserved. A separate PlantEdit-Regression.3dm contains the persistence test edit.

## 2026-11-02 v0.17.2 interaction corrections

Office B only, management MCP 19540 / original Platform 22801. Final build_test 570a8b1c9f9c41048ebdcfe41227230d succeeded: deployment 20261102-185111-c5b0df2825b543abb60c4c8d5a52d021, PID 15672, describe 0.17.2. Initial full Build.ps1 passed (plant-edit0172-full-build.log); later targeted plugin builds and final sandbox build passed with zero warnings/errors. Final package plugin/core/deps were copied from that exact tested deployment. No formal Rhino, library assets or OS mouse input changes.

Root causes: transient empty Eto selection could exit isolation; the native Gumball hover gate could reject plant double-clicks; GetFrustumLine was traversed far-to-near, making ground behind visible trees act like foreground blockers; picking alpha .15 disagreed with native preview .02; preview-only depth separation was missing from picking. Blank double-click had no exit path. Final code scopes picking to the active group, orients rays using CameraDirection, follows wireframe/Xray and per-object mode overrides, matches display alpha/depth, restores semantic list selection and finishes on a no-plant double-click. Context uses temporary pipeline locked-color settings plus gray materials for other plant groups; no document/layer/material colors or persistent display modes are changed.

Test-PlantEditInteraction: 12 actual Eto list double-click / asynchronous empty-selection cycles remain isolated; all 15 plants pass registered native OnMouseDown handlers; a .126-alpha leaf is pickable; native blank double-click exits, viewport double-click re-enters and blank exits again. Original group JSON unchanged, lock markers removed, Modified=false. Test-PlantEditGrey: native rendered before/isolated/after captures; 151498 saturated pixels become neutral and before/after maximum RGB difference is exactly 0. Pipeline locked settings restored exactly. Test-PlantPickOcclusion: a locked owned plane in front blocks the plant, its wireframe object override restores the hit, and a wireframe viewport permits the hit; the owned plane is removed in finally. Existing isolation regression confirms one-member move/copy/cancel and unchanged other rows/object count. Native New from active gray isolation retained PID and rebuilt the two open tools without errors. Raw physical double-click/drag gestures were not injected; actual SDK callbacks and native rendering supplied the evidence.

Retained two failed interaction reports: initial ray test only found six plants; a wire-mode guard alone did not fix the rendered scene. The size-only CaptureToBitmap overload produced wireframe-looking images even though the viewport mode was SceneFlow Demo - Rendered; explicit DisplayAttributes captures corrected that test inference. The actual decisive evidence was ray origin below the scene and direction towards the camera, then 15/15 hits after orienting it. These were assertion failures, not Rhino crashes.

Evidence: artifacts/rhino-B/plant-edit0172/{interaction,grey,grey-pixels,occlusion,isolation,new,ready}.json and rendered-{before,isolated,after}.png. Original model was backed up to Backups/Before-PlantEdit-20261102-134412.3dm before restarting. Final B reopened the original SceneFlow-Hillside-Retreat-PlantEdit-Fixed.3dm, exact group parameters restored, no lock markers, Modified=false, both open tool errors null. No model changes from regression were saved over it.

## 2026-11-02 v0.17.3 single-plant motion

Office B only: final build_test 2fbe72da9c534d81b043e31d84e59137, deployment 20261102-193752-1d4afc708e574409b1676eb0e8fc4c26, PID 39120, original Platform 22801. Targeted build and full Build.ps1 validation/package passed with zero warnings/errors (plant-edit0173-build.log, plant-edit0173-full-build.log). No formal Rhino, library writes or OS pointer input.

The previous GetTransform had an empty OnDynamicDraw while changing a PostDrawObjects billboard, leaving old static feedback and no proper dynamic plant renderer. New begin/end hooks redraw static background once; only the moving member is excluded, its cached mesh/LOD is pinned and its own OnDynamicDraw draws one transformed card. Ctrl-copy retains the original. Rhino foreground feedback is temporary and can draw over context while dragging; committed frames restore ordinary depth/occlusion. FullFrameRedrawDuringGet remains false to avoid regenerating the whole scene on each mouse move. The dynamic renderer owns no document edits and releases the pinned reference on cancel/exit/New.

Valid frozen layouts now commit edited rows/proxy/work stamp immediately, without the .35-second timer, .45-second debounce, carrier meshing/welding or scatter. Carrier/settings/unit key mismatch retains the existing async layout path. Existing custom parameter Undo remains in use. Baseline on the same 15-tree user model: old API submission 7.2867 ms but usable layout 1299.3983 ms, initially busy. New 12 sequential updates: median 11.9777 ms, maximum 46.9569 ms, busy=false and Gumball available immediately each time; other rows unchanged. Single-member copy also immediately ready. These timings describe pose commit availability, not end-to-end pointer latency or GPU FPS.

Test-PlantMotionPreview uses the exact shared DrawDrag renderer through a native DrawForeground harness, the same renderer called by GetPoint.OnDynamicDraw, without injecting pointer gestures or blocking Get. Native frames: 11101 pixels at the old tree rectangle disappear from static background; moving in either direction leaves exactly zero changed pixels there compared with that clean background. New positions draw 7191 / 6930 changed pixels. End/cancel and copy-source retention differ by at most 1/255 at a handful of pixels (mean below .000002); the initial exact-zero restoration assertion was retained as preview-pixels-first.json, then bounded for this observed GPU rounding. Dynamic draw submission measured 2.4302 / 1.7285 ms, not a frame-rate measurement. See commit.json, preview.json and preview-pixels.json in artifacts/rhino-B/plant-edit0173.

Native Undo/Redo, immediate pose Save/Open with identical rows, and New from an active pinned preview all passed with the same PID. Final reopen confirms pinned=null, no active editing/dragging and original user rows/parameters preserved. Physical pointer drag feel still requires the user test; source callbacks, dynamic renderer, pixel output and pose commit path were verified independently.

Before testing the user model was dirty. It was preserved in Backups/Before-PlantEdit-20261102-143500.3dm. Final ready file is %LOCALAPPDATA%/RhinoSceneFlow/Demos/HillsideRetreat/SceneFlow-Hillside-Retreat-PlantMotion-Fixed.3dm, a new copy including those unsaved user edits, with Named View export settings copied. It was natively reopened, 15 trees, Modified=false, no pinned preview. Original PlantEdit-Fixed.3dm was not overwritten. Evidence: baseline/commit/preview/preview-pixels/undo/saved/reopened/new/ready.json and motion-*.png. B is shown with Plants List/properties ready.

## 2026-11-02 v0.17.4 selection-outline shadow fix

Reproduced the reported detached gray tree contour in a full native capture on B PID 39120, with no active drag and no pinned preview. A/B captures on the dirty user model proved the contour depends on both outlines and shadows: its sky ROI contained 2118 pixels below 245; shadows-off, outlines-cleared and plants-suppressed each removed that contour. The scene had no extra tree object. It was not merely a stale mouse feedback buffer.

Move ordinary selection lines from PostDrawObjects into DrawForeground; keep only physical plant meshes in PostDrawObjects. A shared DrawOutline helper enables depth testing and disables depth writing with balanced push/pop/finally for normal and dynamic feedback. This keeps proper UI colors/occlusion while preventing the contour from entering shadow/depth effects. Do not disable legitimate plant/scene shadows as a workaround. Native pipeline stage reference: https://developer.rhino3d.com/api/rhinocommon/type/rhino.display.displaypipeline/ .

Final office B build_test 7b51fb182f8648cdaa5e7e58371d20a8 succeeded: deployment 20261102-200100-038c641b89c043168831e562327e9faf, PID 26944, Platform 22801, plugin 0.17.4. Targeted build plus full Build.ps1 validation/package passed, zero warnings/errors (plant-outline0174-build.log / plant-outline0174-full-build.log). No formal Rhino, shared library writes or OS pointer input.

Test-PlantOutlineShadow native rendered captures: phantom ROI dark-pixel count is now 0 with outlines ON; comparing outlines ON/OFF produces exactly 0 changed pixels outside projected plant rectangles (maximum RGB difference 0). The shadows-on/off control still changes 278493 scene pixels. Green/cyan/orange UI pixels remain 3482/3205/5696. Thus the fix preserves both highlight cues and legitimate scene shadows. Evidence: artifacts/rhino-B/plant-outline0174/{ab-pixels,outline,verified}.json and fixed-{outlined,no-outline,no-shadows}.png. Old full capture and shadow-off/no-outline/no-plants controls retained.

Motion regression passed: 12 immediate moves median 12.1584 ms, maximum 49.4602 ms, ready with Gumball/no pending layout, unchanged other members; copy immediate. Shared dynamic renderer pixel oracle: old position unchanged versus clean background for both directions, copy retains its source exactly and cancel restoration differs by at most 1/255. This is native callback/render testing, not physical pointer gesture or FPS measurement.

Before restart, dirty user changes were saved to Backups/Before-PlantEdit-20261102-145953.3dm. Final model is %LOCALAPPDATA%/RhinoSceneFlow/Demos/HillsideRetreat/SceneFlow-Hillside-Retreat-PlantOutline-Fixed.3dm, preserving those changes and copied Named View export settings. Native reopen verified identical parameters/15 poses, no pinned preview, Modified=false. Resumed the user original isolated group/member (custom:77231c114bf74c93af4dc0d8ee896487) after saving, so temporary locks are not saved to the 3dm. Original PlantMotion-Fixed.3dm remains untouched; ready.json records the final state.

## 2026-11-03 · v0.18.0 AI 后期 Web 工作台（第一阶段）

新增第八个原生 Tool / 命令 RhinoSceneFlowPostProduction；前七个面板 GUID 和顺序保留。独立 Bearer/Host/Origin 校验的 loopback HTTP UI，不新增 MCP。通过原厂 Platform 的 postproduction_start/status 提交文件快照及 UI 线程捕获的当前文档元数据。独立串行解析进程、持久项目/对话/配置；New/Open、面板关闭和 Rhino 退出不结束 Web 服务。

完整 Build.ps1 两次通过，最终日志 artifacts/postproduction-final-build.log，零编译警告/错误，已有 Core/原生 UV/植物/PSD/跨进程库验证通过。开发包已包含 PostProduction 静态资源；离线 ZIP 未生成，旧离线 wheels 缺 PSD 依赖，打包器新增缺失依赖拒绝保护。

真实 HTTP/PSD/文本模型验证 scripts/Test-PostProduction.py：1200×900 Hillside PSD、13 个图层/组、1024 最大块/128 每侧上下文产生 4 个无重叠核心，完整覆盖画布；两种导入、源 SHA256、401/403、配置陈旧 409、媒体白名单、JSON 下载、服务重启后项目/配置/对话保持。最终独立证据 artifacts/postproduction/518a4e198daf4985bb6677974acc48c4/verified.json。--chat 实际使用本机 Codex ChatGPT 登录和演示预览，返回真实描述；没有生图。第一轮测试脚本误将结果 text 字段断言为 reply，修正测试后完整重跑通过，保留原目录。

浏览器原生页面验证分组用途联动、分块 1024→512 后 4→20、保存状态、原始合成预览和真实聊天排队/运行状态；使用浏览器 DOM 接口，不输入系统鼠标。首次选取 size 的 label locator 未匹配，重新观察后以页面实际 #size 控件验证，不当作产品失败。

B 首次部署 20261103-184348-05d3f08d32dc4e26b9321cf6d3d96e4a / PID 45272，公共 MCP 交接、面板和原生 New 通过，文件/对象/Modified 保持。最终部署 20261103-184736-f8fa24cff64147899feeff2c3dc6f4c5；加载任务 eb3fe6fbdda44b8695eed59ef6e381b5 Succeeded，PID 9396，Platform 22801。所有五个 Web 源文件与部署文件 SHA 一致。最终交接项目 1cb1ebf8f64649c2b7fcfac2ac29cfdb，Web PID 41456；原生 Open 已保存的 PlantOutline-Fixed 演示，70 个对象、Modified=false，post 工具重绑且 error=null，服务/PSD 项目仍可访问。证据 artifacts/rhino-B/postproduction018/{handoff,open,new}.json；带 bearer 的 launch-private.json 只在忽略目录，不打印/提交。

最终更新任务 cd907bd77a4e47069383bb690df383f4 曾因旧 PID 45272 CloseTimedOut 失败，备份完成、端口释放但进程未退；失败证据原样保留。通过只读窗口检查实际确认 Update Available（Yes/No）阻塞退出，键盘 Alt+N 拒绝更新后进程退出，未使用系统鼠标、强杀或安装 Rhino 更新。后续 Return 的窗口已消失错误不当作额外操作成功；经理记录仍保留原 CloseTimedOut，未冒称有 NormalExit/code0。确认旧进程不存在后显式提交 test，实际加载最终版本。Native New/Open 的 HTTP 10054 经同 PID/文档/面板重查确认，不当作崩溃。

边界：当前只完成 PSD 导入/原始合成预览、图层用途、GPT 描述、分块规划和 JSON 项目；NetVips/OpenCV、实际分块生图、结构漂移检测、拼接融合、结果 PSD 尚未接入。psd-tools 对复杂 Photoshop 效果有合成限制；第一版限制 8-bit RGB、8192 边长、256 层/组、512 块和 2GB，独立进程不等于系统内存配额隔离。详见 docs/PostProduction.md。

## 2026-11-03 · v0.19.0 实际 AI 后期与 PNG 输出

完整 Build.ps1 通过，零警告/错误（artifacts/postproduction019-full-build.log）。实际生图使用既有 Codex 登录的独立 image-only 执行器，文本描述助手仍禁用工具；没有固定承诺某个图像模型型号。psd-tools、libvips Python 绑定与 OpenCV 已接入；不生成结果 PSD。本次没有制作新版离线 ZIP。

真实 Hillside 测试完成单块→整图复用：共 3 次图像调用（共享风格 1 次、图块 2 次），最终 1200×900 PNG。89,955 个保护像素、821,952 个只读像素及原始 alpha 均通过逐字节核对；258,044 个像素改变。PNG SHA256 a77538cb5a46745e2fd26207bfcb7fc33d608787e7bfc4c7a10360aceeb3e420。原生浏览器下载文件哈希相同。原始生成尺寸与回填尺寸分别报告。边界诊断仅供人工复核，不构成几何不漂移保证。证据 artifacts/postproduction-images/6037710ff7834f34b12138d30b79a723/verified-final.json；示例 artifacts/examples/PostProduction-v019。

保留原两项目的 project.json/source.psd，SHA 完全一致，另建示例项目 d54dfb287159466394f9e4e15799c447。固定夹具融合、来源路径/线程/时间验证、并发原子 JSON、取消/恢复、导入权限与重启持久化均通过。Windows 临时 rename/read sharing 故障已通过唯一临时名和有界重试修复；实际已接受图块恢复时未重生，保留首次失败证据。

Office B channel 1cee488700ad42f59492743cc4a2a3fe，加载任务 3430613e9d464405a7a289ae225e091a Succeeded；deployment 20261103-220417-79c5f26c51b74052891e5a27c8705280，PID 31060，原厂 Platform 22801，插件 0.19.0。原厂 MCP postproduction_request 的 GET 与 POST 实测通过，POST 恢复/融合结果同哈希、无额外生图。Native New/Open 后同 PID，已恢复 PlantOutline-Fixed.3dm，70 个对象、Modified=false，工具 error=null。证据 artifacts/rhino-B/postproduction019/{bridge-verified,bridge-post-verified,ready}.json。未操作正式 Rhino，未使用系统鼠标。

旧 PID 9396 的升级任务 6db231b5a7a5497d86b7b36ac2e7c2e6 曾 CloseTimedOut；备份已完成、端口释放，用户确认选择 No/暂不更新后，确认旧进程退出再加载。保留原超时记录，不冒称 NormalExit/code0。最终独立 Web PID 66816、端口 58945 保持运行，示例比较页面已打开；原有项目与模型不覆盖。


## 2026-11-04 · 家里 B 更新至 v0.19.0

家里 B 0d327c4c84f644f089b73834ffd93cfe，仅通过管理 MCP 19540 构建/加载；任务 153dd948369b4976b28c8c20c4a55105 Succeeded，部署 20261105-041952-9385324b092944bfbb22f579dd97d12f（UTC 名称），PID 147608，原厂 Platform 22801。编译零警告/错误，原生 describe 确认 0.19.0，八个工具全部实例化且 error=null，ChatKit ready。初次测试页名 plants 无效被 API 正常拒绝，改为实际 plantsList 后通过，没有改动产品。

原默认 Python 3.14 venv 缺少新版图像依赖；保留为 %LOCALAPPDATA%/RhinoSceneFlow/chatkit-runtime-before019-20261104，默认路径创建独立 CPython 3.11 venv 并安装两个固定 requirements，pip check 通过。ChatKit SDK 协议（fixture agent，不调用模型）、raster 保护/alpha/排除/融合 pixel oracle、fresh image 来源与 Windows 原子 JSON 竞争检查通过。证据 artifacts/postproduction-raster/73a0e23925ff4f51af98e12979a50ff6/verified.json、artifacts/postproduction-provenance/83ca4d2853e94f69859632b0a77c8382/verified.json。

原厂 MCP postproduction_request /api/status 实测服务 0.19.0、codexAvailable/generationAvailable=true，Web PID 59236；本机 Codex ChatGPT 登录有效。这一轮未消耗生图额度，不把接口能力检查称为新的真实生图测试。当前本机空文档上 Native New/Open 空白夹具/New 通过，同一 PID、八工具重绑健康；10054 后按文档与 PID 重连确认，不当作崩溃。最终空白未命名文档 Modified=false，B 窗口显示且 AI 素材页打开。证据 artifacts/rhino-B/home019/{native-ready,new,open,ready}.json，postproduction019/bridge-verified.json，提交/运行环境日志 artifacts/home019。没有使用系统鼠标、没有部署正式 Rhino、没有修改原材质/植物库、没有制作离线 ZIP。


## 2026-11-07 · v0.19.1 对比线拖动

对比模式新增可聚焦的 DOM slider 中线，Pointer Capture 支持左右拖动、画布外夹紧、取消/丢失捕获释放；箭头 1%、Shift+箭头 10%、Home/End，保留顶部 range。按画布实际矩形而非整个黑色视口计算位置，ResizeObserver 跟随布局尺寸。非对比模式/无结果时隐藏并禁用；不触发分块点击。结果摘要显示复用、无可修改像素、待确认数量。本次没有修改生图提示词/蒙版/融合算法，也没有加入“变化强度”参数。

node scripts/Test-PostProductionCompare.cjs 通过：双向移动/捕获/范围夹紧、键盘、留白和缩放位置、选择不变、无结果隐藏。此为事件/几何测试 harness，不是浏览器实际手势。CUA 本机浏览器 host 和 native pipe 均不可用，未绕过工具做 UI 自动化，未使用系统鼠标。浏览器实际拖拽视觉验收仍待用户操作。

家里 B 管理任务 56d5136797a64b2cbb01fd3870ce7e10 Succeeded，部署 20261107-191419-0f6483f5b5bd4cbd97464a42d8690d94，PID 105960，原厂 Platform 22801。构建零警告/错误，原生 describe 与 postproduction_request /api/status 确认 0.19.1，文档对象/Modified 不变；服务 HTML/JS/CSS 与修改源码逐字节相同。测试前 B 未运行，无替换/关闭用户文档。证据 artifacts/compare0191/interaction-verified.json 与 artifacts/rhino-B/compare0191/verified.json。未消耗生图额度，不宣称新的图像质量测试。


## 2026-11-07 · v0.20.0 Studio 双视图与两阶段渲染

新首页为本机 React/Konva/perfect-freehand Studio，旧页面保留 /legacy。稳定图片 ID、独立画布 pose/frame、列表与画布双向定位、右侧参数/标注/历史、缩略图与离屏裁剪、小地图、手绘压感点/箭头/文字/Label、修改/保护区域、最多四参考图的编号参考板。提交冻结输入；源 PSD 仅在源节点提供图层用途和硬像素保护，生成子节点不贴回原粗模型像素。whole 使用现有实际 image-only runner，detail 直接复用已确认整图，不再生成额外风格图。任务检查/接受/重试、整图中断恢复、描述助手（真实文本、禁工具）、自动保存和工程包、三格式导出、中英文设置及原厂 MCP JSON save/export 均接入。实现/边界见 Studio.md。

完整 Build.ps1 两次通过，零编译警告/错误，Core/UV/植物/PSD/跨进程库检查保持通过；artifacts/boards020-{full,final}-build.log。新 HTTP/文件/worker 验证最终 artifacts/boards020/b3788163214147a2b165f6f8ac857957/verified.json：布局与身份分离、409、防无效 overlap、分层 PSD 像素锁定/结构用途区别、精确 alpha/只读像素、四参考合板、工程包往返与路径穿越拒绝、PNG/JPEG/WebP、JSON 保存导出和语言。queued/waiting cancellation 与冻结快照见 board-invariants/4a2318a226864092bccc2a1df1f483e5/verified.json；测试明确阻塞图像队列，不消费模型。旧 raster/provenance 回归见 postproduction-raster/16168a3cc76c4383b459b92108d5af10 与 postproduction-provenance/8188d3000db64fc2bd489d76669129c6。

真实图像测试目录 artifacts/boards020/d5517c8376e8414db53492f648345fe6：一次整图、三次高清尝试，共四个图片执行请求及四份新 PNG 线程/哈希收据（不当作账户计费统计），另一次真实描述回复。源为明确标注的二维粗略体块夹具，不冒称在 Rhino 建立三维模型。整图补充木饰面、窗框与屋面细节。第一高清输入空白过大导致放大，保留失败；改为实际上下文紧凑补边。初次 Canny 边缘也被错误当作硬保护条带，出现重影，已分离诊断边缘与 alpha 硬保护。最终候选仍触发 P90 人工复核，独立查看后显式接受并合并至 1024×768；不是几何一致性证明。中间 Windows 长临时文件名超过路径限制的融合失败，通过不重复目标 basename 的 UUID 临时文件修复；恢复仅重融合，无额外图片请求。原失败证据和中间输出保留，示例不使用旧重影结果。

前端 web/postproduction/test-dom.cjs 通过，零控制台错误：列表/画布、双向定位、位置不变、小地图、直接中线 pointer/keyboard 事件、语言与预设持久化。此为 jsdom + 模拟 raster context 的组件测试，非真实浏览器视觉/手写屏测试。CUA browser host/native pipe 均不可用，未绕过工具发送鼠标或用其他 GUI 自动化。实际笔压设备、拖拽手感和视觉布局仍需用户实测。

仅家里 B 0d327c4c84f644f089b73834ffd93cfe，管理 19540 / 原厂 Platform 22801。最终任务 21985b95984e44ca9b1b3372ff6d5073 Succeeded，部署 20261107-202624-27ed07c75a214794b4f6b9bc30695272，PID 9940。16 个 Web 资源与源码逐字节一致。八原生工具 error=null；原厂 MCP GET boards / POST save / POST export 通过，PNG 与样例哈希一致，无文件对话框。之前 PID 94604 原生 New/Open/恢复空文档通过，HTTP10054 按同 PID/文档重查；最终部署 RHP 哈希与其一致。最终 PID 9940 八页健康、0 对象、Modified=false。105960、111664、94604 的 exit.json 均 NormalExit/code0；未强杀 Rhino。旧 0.19.1 Web 无项目/活动作业，正常 shutdown 后启动新服务。

持久 Web PID 112316 / port 14602 / version 0.20.0，API 和资源核对通过。测试示例以新画板 13b1c78c8c134e85ace7f2d02dec5a02 导入，三图分别是粗略二维示意、实际 AI 整图和检查后高清；初始界面中文，可在设置切换。工程包和图片 artifacts/examples/Studio-v020。没有覆盖原库/模型或更新正式 Rhino，没有制作新离线 ZIP。原生和发布证据 artifacts/rhino-B/boards020、artifacts/boards020-B；旧 PID94604 的原始验收保留在 verified-pid94604。临时 QA 服务已正常停止，生产 Web 和 B 保持运行。


## 2026-11-07 · v0.21.0 可追溯节点工作流

列表树/折叠和画布连线共享稳定 parentId；原文件后缀保留。创建子级/同级只建立待生成白板，空描述/标注/参考，继承所选配置（原图用默认）。原始输入只读，更新写回同一节点，新结果成功后锁定；撤销回到 baseline。输入快照固定版本，父图更新只使直接子级变紫；草稿黄，两种状态同时保留。生图期间内容禁止编辑，布局不影响生成状态。归档为有效祖先遍历加 AI 意图说明，可逆；不自动恢复像素。默认2备份/+3独立扩容/成功后自动清理/手动删除/配置签出及只读预览导出；引用字节不物理删除。读旧板时稳定迁移，保存时落盘。输入检查可定位原始来源链。描述助手原先使用 reply、实际返回 text 的字段不一致在真实归档测试中暴露，已统一并成功复测。首次失败日志保留。

Build.ps1 全验证通过，零警告/错误，artifacts/workflow021-build.log；后续最终管理构建也零警告/错误。HTTP/PSD/像素/四参考板/包往返/格式/权限回归 artifacts/boards020/b8e16093e83144da8c67cf2a062ddd6c。状态/备份/归档/取消/包测试 artifacts/workflow021/3ef8dce3952b4c3fb84cbdb6735d92fd；queued/waiting cancellation artifacts/board-invariants/81313476bf8e40f79052caee3f5fbce0。组件测试 artifacts/workflow021-http/0ef0d14ed33f4ccab41e313bd18f4576/dom-verified.json：反复选图、列表/画布、锁定、草稿自动保存/撤销、同级白板、树折叠，零 console errors。该测试使用 jsdom/模拟 canvas，不是实际浏览器视觉和设备手势验收；黑屏修复针对选择加载顺序、预览重挂载及画布自动定位，仍需用户视觉复测。

独立合成建筑夹具实际请求1次 image-only 生成，来源新图收据 newImage=true，267379像素改变；没有修改用户案例。artifacts/boards020/8b4b2f66bb054139af29591e05254527/verified.json。归档执行两次实际禁工具文本任务，第一次模型已返回文本但字段不匹配失败；修复后 archive-verified.json 证明 AI摘要、后代变紫、解除归档均通过，未再调用图片模型。

仅家里 B 0d327c4c84f644f089b73834ffd93cfe，管理19540/原厂Platform22801。最终任务669d8889963446e3a687d80537c06881 Succeeded；deployment 20261107-220123-eda2bc0f718f44c9a9f41e7c7a41d88f，PID121792，describe=0.21.0，8工具error=null。真实 New/Open/New 后同PID，原生空白未命名文档0对象/Modified=false，10054按新文档重连检查，不认定崩溃。Web PID21864/port4962/version0.21.0；16资源与最终源码逐字节匹配。原山地案例9916447c152344a3a7b654d6eefa133a仍2节点，asset/preview/尺寸均与更新前备份一致；已打开列表原图。证据 artifacts/rhino-B/workflow021；更新前完整画板资产在 artifacts/workflow021-before-update。未改正式Rhino、未用鼠标、未创建新离线ZIP；临时测试服务已正常shutdown。


## 2026-11-07 · 待生成白板重影修复

用户截图复现的原因：Compare 对所有带父级的节点默认启用 compare，白板也画了父级底图；pendingBoard 又放了 opacity .25 的嵌套 img，而原 CSS 仅约束 .comparison>img，嵌套图保持固有大小、居中后与底图错位。源预览 hash 与 input.preview 相同，输入文件没有重影。修复为 pending 只画一张正常比例输入图，明确 absolute/inset/100%/object-fit；禁用结果对比和混合、移除中央文字遮挡，画布白板也不再淡化输入。pending→completed 后才恢复对比。

web/postproduction/test-workflow-dom.cjs 扩展并通过：唯一 img、无底图/结果 canvas/对比线、CSS 填框、相同节点白板转结果及原有列表/锁定/保存回归，零 console errors。证据 artifacts/workflow021-http/efedb9e45359401d89af53d88331759b/dom-verified.json；这是 jsdom 组件/CSS 断言，不是浏览器实际截图。未消费生图额度。

管理 MCP B build 1c0f7b93e830406ca89a16eff8803129 Succeeded，零警告/错误，新 payload 20261107-222310-f5b590228a41417bae98bbb29c47240c。仅把已核对的 JS/CSS/许可证静态文件热更新到当前 B 原生 .rhp 所在目录；原文件已备份 artifacts/preview021-before。Rhino PID121792、Web PID21864 均未重启；实际 HTTP 返回与源文件逐字节相同，案例 board JSON 前后一致。证据 artifacts/rhino-B/workflow021/preview-hotfix-verified.json。刷新页面即可载入，正式 Rhino 未改动。


## 2026-11-07 · v0.22.0 理解框布局、历史与鼠标交互

主体按理解框占位，分层子树布局、新建整齐放置、移动与调整frame避让、附件跟随。前后端同算法；拖动暂态布局/端口实时跟随，松开才提交。每条子分支−/+端口在理解框边缘；画布/列表独立折叠，折叠整理。单击不缩放，显式定位。删除为级联软删除；持久Undo/Redo原子存于board.json，Ctrl+Z/Ctrl+R，版本发布为历史边界，源像素不覆写。右键捕获平移/取消/原地菜单，滚轮预览滚动与可选上一张下一张设置。

完整 Build.ps1 通过，零警告/错误：artifacts/layout022-build.log。HTTP/worker/PSD/保护像素/包/导出回归 artifacts/boards020/4052183d9ab14e3f932283f51212850e；取消/冻结输入 board-invariants/d6f60ae4f21742ffa4eac78aaf3869f4。布局/持久历史/删除/框避让/新建单步undo：artifacts/layout022/b09470a9515242449727ee803cae1363/{verified,js-verified}.json，80节点Python/JS精确一致、12次拖动样本无框重叠。组件事件 artifacts/workflow021-http/fbb5dc4d1fec4d33bcb6e09522ddbfbf/layout-dom-verified.json：真实Konva fire驱动拖动/Transform，松开前连线更新、仅松开落盘、无变换放大反馈、独立折叠、CtrlZ/CtrlR删除/框调整、右键只改相机/菜单保留、滚轮设置等，零console错误。这是jsdom/模拟canvas，不是浏览器视觉/手写设备验收；本轮0模型请求。

B 19540管理任务9c38e006f8ce432188d36ccd9afde2ed成功，部署20261107-224457-7be1ee6a18c24e10a91d41b260a7e3c5，PID113512。追加右键/滚轮后管理build 9447d61f025744cbae92ebbeb48967f5成功，最终源payload 20261107-224754-9dac3b6dd7094cbca6174af64e529493；RHP哈希与活动实例相同，启动Web前同步17资源到当前B payload。原厂Platform22801确认describe0.22、八工具error=null；原生New/Open/New同PID、0对象/Modified=false，10054按新文档重连验证。Web113816/9320/version0.22；实际HTTP JS/CSS与源码一致。

原山地案例6节点，通过原厂MCP实际执行arrange→undo→redo，框无重叠，所有像素/预览/配置/标注/父级/输入/版本/来源不变。已在画布概览打开；只调整布局和相机。更新前完整画板在artifacts/layout022-before；验收与MCP往返在artifacts/rhino-B/layout022/verified.json及bridge-*.json。旧0.21 Web正常shutdown；临时组件服务已关闭。未使用系统鼠标，未改正式Rhino，未生成新离线ZIP。


## 2026-11-07 · 列表默认翻图与“平滑”连续浏览

根据用户澄清，默认滚轮切换上一张/下一张，预览工具栏增加“平滑”开关。开启时沿列表当前顺序把图片纵向排列成连续页面；原生滚动，不以固定间隔强制切图。图片按宽高比占位，IntersectionObserver仅加载可见区域及400px预取，预览使用单层像素Canvas，无父图叠加。滚动不更换编辑对象；点击卡片选中，从侧栏选择则定位卡片；“单图对比”关闭平滑并进入所选图的对比。参考/白板仍显示各自身份，备份查看保持单独预览。设置与工具栏共享持久选项。旧scroll含义为滚动单张图，增加listWheelVersion=2一次迁移到默认navigate，此后保留用户选择。

test-smooth-dom.cjs通过：默认前后翻图、开关/持久化、纵向卡片顺序、单层预览、滚动不改编辑目标、卡片选中不跳动、侧栏定位、返回对比、像素/参数/来源不变；零console错误。证据 artifacts/workflow021-http/03b410221db64121a1dfd42e41a95862/smooth-verified.json。更新后的完整画布/历史/右键事件回归 artifacts/workflow021-http/ce4bdbd2b84140f4bd063847742ef50a/layout-dom-verified.json也通过。以上为jsdom/模拟绘图，不是浏览器视觉验收。0模型请求。

管理B build aa11dad7437c42ee9de72e3b9a1ad3bb成功，零警告/错误，payload20261107-230948-8731f08e115249eab9e11fd5c25a8ea5。确认RHP与活动B哈希一致后仅同步Web模块/资源，不重启Rhino113512；旧服务shutdown初次立即Ensure复用了退出中的旧服务，保留连接拒绝证据，重试启动后确认新Web115892/7446、版本0.22、listWheelVersion2/default navigate、HTTP JS/CSS与源码一致。山地案例节点数据前后一致，只切为列表原图供试用。验收 artifacts/rhino-B/smooth022/verified.json。临时服务关闭；正式Rhino不变，没有ZIP。


## 2026-11-07 · 白板显示、侧栏定位与折叠样式修正

待生成结果改为白色：单图和平滑卡片是左白/右固定输入，通用WipeHandle拖动/键盘控制裁切；画布不加载/绘制源CanvasImage，缩略图同样白色，输入检查仍显示真实输入。所有底层资产、模型输入和参数不变。侧栏新增默认开启autoLocate，控制侧栏对画布/连续列表的定位；画布普通点击仍不缩放。隐藏祖先通过layout reveal展开，仅修改画布折叠状态。

找到实际折叠UI失效原因：通用.resource>button把按钮设为opacity0/absolute/right-bottom，树按钮与定位按钮重叠。新增.resource>.treeToggle明确static/opacity1、叶子占位，测试真实CSS级联，不仅测试点击函数。移除搜索时忽略collapsed的逻辑。

组件/样式/Konva regression artifacts/workflow021-http/0783e285418749d28829b72088e2d1a8/blank-focus-verified.json：左右裁切/拖动、纯白Rect与0个Image、白缩略图、自动定位开关/展开隐藏路径、画布点击不缩放、可见static折叠按钮真正隐藏子项、画布/列表独立、平滑白板对比、输入不变；零console错误。旧工作流组件测试更新为新规范并通过，证据workflow021-http/6b1d413ded3640d6ac06689f83f1a04a/dom-verified.json。布局/前后端80节点parity回归layout022/7c6b59322989474ea47089dfbc15a346通过。以上是jsdom/模拟绘图，非实际浏览器视觉验收；0模型调用。

B管理build 1b9b266bfa9d4d99b330b15739c38293成功，零警告/错误；payload20261107-231943-c3752f26704e4de4a98fa1ab651c9d4c。与活动B的RHP哈希一致，仅同步Web并等待旧服务退出后重启Web，Rhino113512未重启，8工具健康/0对象/Modified=false。Web120528/8647，实际HTTP JS/CSS与源一致，autoLocate默认true。案例6节点数据前后完全一致，仅切换列表并选中已有白板0f5fe4b8b51648018795353119d5652d展示。artifacts/rhino-B/blank022/{before,verified,browser}.json保留证据。无正式Rhino修改，无ZIP，临时服务已关闭。


## 2026-11-07 · 切图淡入与平滑模式结果对比

根因：Compare按node/backup key反复挂载，available先重置900×600再由ResizeObserver测实际尺寸；draftNotice和工具栏换行也改变可用高度。修复为按board挂载、测量初值0且保留，固定工具栏40px、白板提示改行内。decodedPreview原子等待结果/父级输入解码，旧帧保留到新帧就绪；过期请求忽略。仅opacity140ms过渡，旧帧独立尺寸居中，170ms释放；Canvas在layout effect绘制。新旧图不同宽高比各自fit，不对旧图套新比例。快速切换不回放迟到图片。

平滑FeedImage此前仅pending渲染wipe，已生成图片且blend100时连父图都未加载。现在有input的可见卡片均加载固定输入，左结果/右输入互补裁切，共用WipeHandle；pending仍左白，根图不伪造父图。保持懒加载、卡片选择及参数不变。

test-preview-transition-dom.cjs最终证据 workflow021-http/80ff6f5bcba44e2f854646a806174fcc/preview-transition-verified.json：1400×900 viewport只测量一次，延迟加载期间旧图尺寸保持、迟到结果忽略、140ms淡入/旧帧清理、已生成卡片wipe拖动与裁切、源根无伪造对比、节点数据不变。白板/定位/折叠回归 workflow021-http/87ee5ea459004ddb97ab5eae36bef9e5/blank-focus-verified.json；流程组件 workflow021-http/67e3acb43b764042aeccb68e2a6ccfe9/dom-verified.json通过，均零console错误。均为jsdom/模拟canvas，不是浏览器动画视觉验收。没有调用模型。

B管理build4f2939b8663547d0a1e8f120d8ab6a11成功，零警告/错误；payload20261107-233341-ef6042389c6a4a64a578f67dc4bd6f2a。只原子热更新活动B的JS/CSS/许可文件，旧资源已备份；Rhino113512与Web120528/8647均不重启。实际HTTP资源与源码匹配，案例JSON前后一致。证据 artifacts/rhino-B/fade022/verified.json。刷新现有页面载入，不需重生成图片。正式Rhino未改，0图像/文本模型请求，无ZIP。

## 2026-11-07 · 输入模板、删除提示与恢复默认

最终构建 6e8357548d804852ae044b9d129e48db 成功，零警告／错误。工作流测试 `artifacts/workflow021/e36cd57f6ced439fb390fd355da20882/verified.json`、布局 `artifacts/layout022/3a39ba6333be4f0fbdc93ed48a18265b/verified.json`、取消／快照 `artifacts/board-invariants/d659c96c07314751946068a5fcca8fa2/verified.json` 通过。组件 `artifacts/workflow021-http/6e79001829644f389d6fd1352230ed9c/input-defaults-verified.json` 验证原图模板、描述继承、参数逐项／整体复位、删除不再提示／取消／撤销；连续重置暴露的旧闭包覆盖问题已修复。工作流组件最终 `artifacts/workflow021-http/43ad38fca60a4b308ea9d1c35889603d/dom-verified.json` 通过，零 console errors。组件使用 jsdom／模拟 Canvas，不是实际浏览器视觉验收；没有调用生图模型。

B 仅更新 Web 资源和 Python worker，无需重启 Rhino。真实案例全部节点逐字段校验，只有原图 locked 改为 false，其像素和既有描述／参数／版本等保留。资源与源码完全一致，见 `artifacts/rhino-B/defaults022/verified.json`。原图只读的旧记录指像素保护，现行配置可编辑规则以本节为准。

2026-11-07 补充：原始输入始终不锁定。描述清空时机改为成功发布结果；创建草稿、失败、取消不清空，任务期间新写的描述不被旧任务覆盖。工作流回归 `artifacts/workflow021/06b7e64f8430464897aaf835411918b4` 通过；独立合成像素验证清空时机与并发新描述保护，无模型调用。B 两个 Python 模块同步后优雅重启 Web，未重启 Rhino。

## 2026-11-07 · 画布九工具

`web/postproduction/test-tools-browser.cjs` 使用独立 fixture 和真实无界面 Edge，通过浏览器原生鼠标／笔事件和命中检测验证九工具、选图不缩放、图上开始平移、锁定提示、解锁后 Transformer、正确笔画归属、文字／Label 保存、笔压／单点、pointercancel 丢弃、原生拖动与理解框缩放。证据 `artifacts/workflow021-http/16c668f9a12449fabe22a46e4fd38f4f/tools-browser-verified.json` 和截图。初次探针确认原图绘画可用，主要修正静默锁定和旧选图绑定等问题；未宣称每个工具此前都失效。保留前期测试失败（离屏点击、压力浮点精度和合成指针捕获）；最终改为原生 CDP 笔事件，无 page errors。布局组件回归 `artifacts/workflow021-http/cc1edf73b1154230b6b6a8d51987c361/layout-dom-verified.json` 通过。没有使用系统鼠标或生图模型。

管理构建 `aedc6c1484cd4eed8af92a5d1563b52b` 零警告／错误。B 静态资源精确核对，原生哈希相同，画板所有字段未改；真实 B 页面用 headless Edge 验证九按钮激活，无脚本错误，未在用户图片绘画，见 `artifacts/rhino-B/tools022`。仅模拟笔事件，尚非实体手绘屏设备验收。

## 2026-11-07 · 标注二次编辑与笔刷大小

新增 `web/postproduction/test-annotation-edit-browser.cjs`，真实 headless Edge 中验证六类已有标注的命中选择、独立拖动、角点缩放、压力与 id 保留、修改原文字、画前／画后笔刷大小、Delete 仅删标注、Undo／Redo、空白取消选择和刷新持久化；原始图片 asset 与 pose 未变，零 page errors／模型调用。最终证据 `artifacts/workflow021-http/2ed041281bdf40f58b698b5dd68595c2/annotation-edit-browser-verified.json`，并人工查看该目录下总图与 selected 截图。前期 anchor 测试点选到了控制柄外缘、以及工具切换后的异步 hit canvas 未绘制完成，保留失败记录；最终在真实控制柄中心命中并等待绘制帧。控制行改为固定高度，避免选中时画布跳动。鼠标事件冒泡已隔离，未使用系统鼠标。

九工具 native hit regression `artifacts/workflow021-http/bbf0f7b823d94fdca0118fcc63467f07/tools-browser-verified.json`、Python／JS 80节点布局一致性回归通过。测试工具使用临时安装的 `artifacts/browser-harness` playwright-core 和系统 Edge，未增加产品运行依赖。原九工具测试现从图片空白处拖动整图，因为命中已有标注会编辑该标注。

管理构建 `921ebe89bd824d139c95b9b9017477a2` 成功，零编译警告／错误。B 资源精确一致、原生哈希一致、真实画板更新前后完全相同；真实 B 浏览器重新加载九工具无 page errors，见 `artifacts/rhino-B/annotation022`。实体手绘屏尚未在本机做设备验收。

## 2026-11-07 · 文字原位编辑

`web/postproduction/test-inline-text-browser.cjs` 使用真实无界面 Edge 验证无 modal、双击原位编辑、隐藏旧文字防重影、中文多行、composition键不提交、缩放对齐、点击外部提交、Esc 取消并恢复选择柄、新建文字／Label、取消不产生空标注、同一 id、刷新持久化与原图像素身份／pose 不变。最终证据 `artifacts/workflow021-http/dc22aaa383d44fc1b0516cfa245fd362/inline-text-browser-verified.json`，已查看 editing 截图，无 page errors／模型调用。composition 使用合成键事件检查分支，未宣称实体输入法／手绘屏全面验收。初次新建测试暴露 pointerdown 默认焦点导致原位框立即 blur，现已 preventDefault 修复，保留失败记录。

标注编辑回归 `artifacts/workflow021-http/35dad762b7a24938864aa8236a6d46a5/annotation-edit-browser-verified.json`、九工具回归 `artifacts/workflow021-http/3e1b2fc3c4094c1381b4b8ab826fe0c7/tools-browser-verified.json` 通过；旧测试改为原位 textarea 完成编辑。管理构建 `1ea197453a9a41938aa5453ac1ff8957` 成功，零编译警告／错误。B 静态更新、真实画板完全保留与浏览器无错误证据 `artifacts/rhino-B/inline022`；未在用户案例写测试文字，未用系统鼠标。

## 2026-11-07 · 空间考虑框、闭合遮罩与父级底图

`Test-CanvasContext.py` 最终 `artifacts/canvas-context/65e062d628e24841a625826537710ee5/verified.json`：框内纳入／框外排除、扩框吸纳、参考不属于计算主体、主图移动带随资源／框外不动、applyParent 保留草稿／不造生成／Undo/Redo、闭合修改区内部像素与保护优先、空间图／箭头及参考坐标、工程包资源往返。检查了 raster/markup.png，箭头与旁边文字／参考保持位置关系。纯合成图，无图像模型调用。

真实 Edge 最终 `artifacts/workflow021-http/1b9eeabc318a499db4b7cf9eaa40b43c/spatial-canvas-browser-verified.json`：T/Label 可见区别、浅 Hatch、框外自由笔迹／文字、Clipboard PNG 为 detached resource、没有资源框／隐式扩框、扩框吸纳、跟随移动、父图填入草稿，零 page errors。查看了前次一致场景 `1c3f50a1e927465582ad853953b1341c/hatch-resources-browser.png`。没有用系统鼠标，没有在真实案例加测试资源。最初 fixture 的文字实际延伸进框，断言已按文字完整 bounds 修正；另保留测试读取未设置 dash 的失败记录。

既有回归：工作流 `artifacts/workflow021/22be98aa237141c5a6b8659e3addbfdd`、布局／持久 Undo `artifacts/layout022/20e485c1c43f438f86ef9d54938da5c4`、取消／快照 `artifacts/board-invariants/c2a9f5654c1e4667aafa7a72df4eae7f`、PSD/raster/只读像素/工程包 `artifacts/boards020/2c0520534278443dba77f9c36ca0849e` 均通过，80节点 JS/Python 布局一致性通过。旧浏览器用例中“新绘画存到选中节点 annotations”这一断言由新的空间用例取代；既有节点标注的兼容读取仍保留。没有实际调用模型检验本次语义生成质量，不能把上下文传递正确表述为模型必然理解正确。

管理构建 `5ab97fca3c634bb9a5516560600692f4` 零警告／错误。B 仅优雅重启 Web，原生 PID113512 不变；新 Web PID86356。真实案例比较仅允许 marks 默认值与旧 reference.parentId/inputChanged 的迁移，其余字段完全一致；静态文件及 context API 精确验证，真实 B 页面九工具加载无错误，见 `artifacts/rhino-B/spatial022`。

## 2026-11-07 · 标注删除目标修复

诊断：顶部删除一直调用图片 requestDelete，右键捕获只找 image-node；因此键盘已有标注分支，但顶部／右键未跟随标注选择。真实案例只读检查确认截图文字是原始图的旧 annotations，原图未锁定。修复统一 deleteAnnotation，按 nodeId/id 固定目标，优先命中标注／Transformer；同时覆盖独立 canvas mark、无主体、侧栏行和晚到的编辑框 blur。

真实 headless Edge `artifacts/workflow021-http/edc71474c37748b48a72518de2b074ea/annotation-delete-browser-verified.json` 验证图片上方旧文字、独立文字、顶部／键盘／右键／选框柄／侧栏／× 删除、Undo、编辑中删除并刷新不复活、无主体删除、图片与像素身份保留；零 page errors，无图像模型调用。所有删除都发生于合成隔离测试，没有删除用户截图中的原文字。

管理构建 `9738fc7868e242f09a44fac5c6bce428` 零警告／错误。B 仅静态更新，原生 RHP 哈希、Rhino 与 Web PID 保持不变；真实画板所有字段原样保留。B 浏览器加载九工具无错误，证据 `artifacts/rhino-B/delete022`。

## 2026-11-07 · 边界免解锁、参考图缩略图框与资源转换

`artifacts/reference-gallery/840336ddb592416caf39bd0bce478678/verified.json`：锁定状态下 frame 可改、params 仍拒绝、重新锁定保留描述与参数、原始输入不锁、参考删除保持主体布局和 anchor、资源转换保留 ID/asset 并可 Undo、独立自动定位偏好及类型验证。

真实 Edge 最终 `artifacts/workflow021-http/d6b2a5b59e924bd98526ed37cdc01a28/reference-gallery-browser-verified.json`：从列表直接进入边界编辑、原生控制柄缩放锁定节点而锁不变、左侧不显示参考、缩略图在禁用内容区域外、双向选择且主图设置保留、默认不缩放／可开关并持久化、锁定主图中的参考可删除并不重排主体、Undo、显式转换后才入列表、转换撤销和手动重新锁定。零 page errors、无模型调用。查看了同等场景 `f7ebdd74a5d1457f905a661d4930a775/reference-gallery-browser.png`。初次测试用 isDisabled 检查 fieldset 的假阴性保留；改为 DOM disabled 属性直接断言。

原工作流 `artifacts/workflow021/216c0a64677c4208af83cb59bde4732f`、空间／mask／工程包 `artifacts/canvas-context/6767c9c80ea04daca722dbfff0ecf7bb`、布局历史 `artifacts/layout022/dea9b6c8c2444c18a4578305f8d57f83` 以及 80 节点 JS/Python 一致性通过。

管理构建 `75261a3b9c83495e9cf231af9b123d97` 和列表边界入口最终构建 `e67ff4a007074dab978c7faa25d426e2` 均零警告／错误。B Web 后台优雅重启一次至 PID103296，Rhino PID113512 未重启；最后入口修正仅静态更新。真实画板更新前后逐字段一致，资源文件逐字节匹配，B 浏览器加载无错误，证据 `artifacts/rhino-B/gallery022`。所有移动、转换和删除测试均为隔离测试资产，未修改真实案例。


## 2026-11-08 · PhotoCraft 单份编辑参考层

集成官方 PhotoCraft 0.21.0 Web/Wasm；发行 ZIP SHA256 `3cf893112507ac192c921e0223a3bd5404a24b3dcf94e7a37d43f5eba2032286`，15 个上游文件逐字节不变，增加独立宿主适配器与补充许可证。厂商发行包 app/snippets 相对路径由静态路由别名补齐，未改写原版 JS/Wasm。构建包含完整 vendor 目录，非运行时下载占位。

`web/postproduction/test-photocraft-browser.cjs`：真实 headless Edge + 官方 Wasm，原生画笔两次修改、保存/返回、再次载入原编辑 PSD、单槽替换、取消不应用、刷新恢复缩略图、参考层/原图 wipe 对比；证据 `artifacts/workflow021-http/e347df3ac2b04a00856a02c2cb6fa73f/photocraft-browser-verified.json`。参考图修改像素分别 1864 / 3728，原始 asset、versionId、versions、节点数量均不变。测试没有使用系统鼠标。

`Test-PhotoCraftReference.py` 最新证据 `artifacts/photocraft-reference/fab65f6d2b1b4b8cafccadb33cf113c1/verified.json`：精确项目往返、并发旧会话 409、重复提交 409、异常 PSD 尺寸 400、取消清理、JSON apply-file 只读输入、单槽排除于画板 undo、工程包往返、原图变化停用参考、原始/备份保持、raster base 像素与干净输入完全相等且编号参考板实际生成。Undo 保留当前槽位，并重新保留未被更新的参考指引的 dirty 状态。

回归通过：BoardWorkflow `f9062db5cfb7438c845f72d0bcf6fccb`、BoardLayout `dc30af9ef1e4436ebeafde6e66d0c74d`、CanvasContext `96f728a0a57d443185120c27ecd979d1`、ReferenceGallery `42ea33704c24484eb2ef6877871d9704`、BoardInvariants `39f28e1dd88a4326864e96b5feed9d6b`、PostProductionBoards `3af85db7c084424cab131e5bc81f38e9`，及真实 Edge 的参考图库/锁定/框编辑回归。全部无图像模型调用。本次验证的是实际编辑往返与生成输入准备，不声称 AI 已遵循这些新增标注生成新图；高级 PhotoCraft 功能的 PSD 无损往返没有全覆盖。

B 最终构建 `5abd54a2d16f4a9585c6ccf94faeca18` 零警告零错误；Web 资源与 source/built/active/package 全量一致。真实案例只打开 PhotoCraft 后取消，逐字段数据保持（8 节点含已删除节点）；实际涂画/应用在隔离 fixture 完成。证据 `artifacts/rhino-B/photocraft022`。


## 2026-11-08 · 编辑参考层显示开关

`test-reference-visibility-browser.cjs` 在真实 headless Edge 中验证列表／平滑列表／画布和小眼睛，证据 `artifacts/workflow021-http/2ae703077e634684a123cd624897d856/reference-visibility-verified.json`。实际截图像素判定结果区红色叠加、输入区保持原始绿色、透明部分保留结果绿色；保留 wipe 值、刷新后仍隐藏、AI 参考启用独立、Konva 叠加层 listening=false 且不阻挡选择。context、dirty、versions、历史数量不变；实际导出的 PNG 中心仍为原结果像素，未烘入参考层。

真实官方 PhotoCraft 再编辑/替换保留隐藏状态通过：`artifacts/workflow021-http/ba96c31489b64c5590554fa542e2077b/photocraft-browser-verified.json`；配套输入／工程包／会话保护回归 `artifacts/photocraft-reference/16cffa4e763d4967afb17df8efbb52a0/verified.json`，隐藏的参考仍实际进入生成准备的 reference-sheet。BoardWorkflow `dbdf584f68c5413c999ed92fd60787d9`、ReferenceGallery `b9caf212fd5f48d59e95857f10a1a88d`、CanvasContext `74bb753706e74def8a54d76fb48be0f7` 通过。全部无图像模型调用。

B 上用户已经编辑的原始图参考层（不是新造的测试层）默认显示，源码／构建／活动部署一致；读取并显示后真实案例逐字段未变。最终证据 `artifacts/rhino-B/reference-visibility022`，构建 `0a16f7477666468f8076f5d6af22d041` 零警告零错误。


## 2026-11-09 ? ?? B ????

? Sandbox-B.md ??????? dc8913c865ad44cca3d7c565ba13e935 ???? 0.22.0??? MCP ? Web ??/PhotoCraft ?? SHA ??????????????????? MCP 0.3.0 ???0.4.0 ??? DLL ????????????????????/??????? Rhino ????????????????????????????????????????? artifacts/rhino-B/company022/verified.json?

## 2026-11-09 · AI 任务流程 0.22.1

scripts/Build.ps1 完整通过，零编译警告/错误，Core/UV/随机贴图/植物/PSD/跨进程材质库检查通过，日志 artifacts/taskflow0221-build.log。最终 B 发布见 Sandbox-B.md，原生版本/原厂 JSON MCP/工具栏/活动静态文件均实测，不把浏览器检查称为新的模型画质验证。

新增 Test-TaskInputs.py：artifacts/task-inputs/67eaba377473484b87ca54b7ec67186f/verified.json，验证原子高清草稿、无描述高清、预检只读、真实 raster、最新输入解析、固定比较输入、归档跳过和陈旧检查拒绝。实际 Edge + HTTP 的 test-task-flow-browser.cjs 最终证据 artifacts/workflow021-http/a89bc2fb281243f4baa515fa781f34ab/task-flow-verified.json：高清/同级来源、描述首屏、真实输入/mask、辅助标注底图不标 AI 结果、关闭预检无迟到弹回、画布框入口、原始像素/版本保留，零 page errors / 模型调用。

既有回归通过：BoardWorkflow b794c4b475964501bca4791feef2983a；CanvasContext 537d1b17e198471097351473ef88a99a；BoardInvariants bd9df112492546139e8f50bfdd6a3ae8；ReferenceGallery 5fa747b8c98e4edda4ba5bbaa831ecff；BoardLayout 15d5a2a3a3584bf79afab8cd2e729c5d；PostProductionBoards 9eee0466bd8c40069e1fc477a6af6d7f。

参考层实际像素/锁定/左右对比/刷新/平滑/画布/选择/导出回归：artifacts/workflow021-http/57c61b1ce8964abfbaec8123f2ec4dcf/reference-visibility-verified.json。原位文字（中文、多行、composition 分支、zoom、blur/Esc、刷新、像素不变）：artifacts/workflow021-http/3e14cb44dcb045088e74f30a198e3c84/inline-text-browser-verified.json。旧测试把新文字仍断言成 per-node annotations，首次失败证据保留 1c700bc888e24763b9c88ed8ed1336df；实际文字已正确写入 world-space board.marks。断言已改为恰好一份 world mark、正确世界坐标，原两份 legacy marks 不变，未改产品去迎合旧断言。

最终 Hillside 页面实测 artifacts/ui-audit-20261109/release-case-verified.json 与 release-case-{list,mask,canvas}.png；原厂桥预检 artifacts/rhino-B/taskflow0221/bridge.json。全部为输入/界面/保护语义验证，零新增模型调用。测试中九个自有 idle fixture 服务已正常 shutdown，未结束用户服务/进程来清理测试。

## 2026-11-10 · 0.22.5 UI／恢复与跨工具验证

scripts/Build.ps1 全构建及 Core 验证通过；新增 Test-TaskRestore 覆盖 AI 分组恢复、显示不变、共享内容继续 pending、旧 baseline／backup 的默认字段，Test-TaskInputs 验证整图及高清预检的准确输出尺寸。BoardWorkflow、CanvasContext、ReferenceGallery、BoardInvariants、GuideGates、RasterStability 均通过。

无界面真实 Edge 最终十条流程通过（artifacts/ux-audit-20261110/browser-verified.json）：tools、annotation-edit、inline-text、spatial-canvas、annotation-delete、reference-gallery、edit-scope、task-flow、task-restoration、reference-visibility；page errors 检查通过，认证 favicon 的 401 单独记录。首次旧定位器／旧 world-mark schema／不独立 fixture 的失败保留；按当前产品契约更新脚本后重跑，不将首次失败掩盖。PhotoCraft 普通编辑两次及特殊图层实际浏览器 roundtrip、独立像素和过期会话验证通过。

B 原生：八面板、实时材质选择／队列冻结／空选择／图层范围、真实尺度 UV 与失效、Plants List 双向选择、12 次隔离进入／15 株拾取／空白双击退出、单株移动缩放镜像取消通过。600×450 真实多通道 PSD 经 psd-tools 检查；两个完整 New/Open 周期最终八工具重绑定、同 PID。只读布局捕获不算 HWND WebView 或视口完整视觉 QA，558 ms 的单株测试调用不算帧率基准。

真实 AI：独立案例 1 次整图调用，53.76 秒；新 PNG receipt SHA 校验，48,807 个只读像素与 alpha 精确保持；输出 600×450。另存工程 ZIP 及资产包含校验通过。未重新运行原生植物／材质 AI 新生成、真实手绘屏硬件、万株植物性能、真实 4K 或全部错误场景；不宣称全插件所有组合无 Bug。详细矩阵和待办见 UX-Audit-2026-11-10.md。
# 2026-11-10 · 0.22.6 画板切换与原生后期面板

修复异步保存后重新读取 select 事件目标值导致无法切板；在事件发生时固定目标，保存失败保留当前画板与编辑内容。真实 headless Edge / HTTP 回归覆盖空板往返、有待保存描述、延迟加载、保存失败及重试、刷新恢复，零模型调用。证据：artifacts/workflow021-http/3b158413816545f09a7d3431a6b3cbcb/board-switch-verified.json。

完整 Build.ps1 通过。B 原生 0.22.6 实测刷新保留 PSD 选择、无文件时禁用导入及显示导出入口；360/520/820 宽度只读 WPF 布局捕获，9 个嵌入图标互不相同。实际本机 Web 服务空板与案例往返通过，全部五个 board.json SHA 与偏好保持不变。证据 artifacts/board-switch-0226/{native-panel-verified,live-verified}.json。既有自定义 RUI 不自动覆盖；新包图标已更新，已注册原生侧栏使用新图标。

## 2026-11-11 · 0.22.7 原生工具 UI 与 ChatKit 主题

完整 Build.ps1 通过（零编译警告／错误，Core 验证全过），最终 B 部署、构建包与源码 ChatKit HTML / 插件二进制一致。ChatKit 使用官方主题配置，原生读取 Rhino PanelBackground / EditBoxBackground 与文字色，每秒仅在颜色变化时更新；更新不重建 WebView，不重载对话。独立浏览器没有 Rhino 宿主时跟随 prefers-color-scheme。修复初始 DOM 命名属性早于 SDK 就绪、setOptions 需要完整配置两项真实组件问题，不能只验证自有 CSS 背景。

真实 headless Edge + 官方 ChatKit：深浅色往返、系统媒体主题变化、composer 草稿及 iframe 身份保留、初始短欢迎语、地址清除认证 query，通过且 page errors 为空。原生 WebView2 SDK 截图及状态确认 ready=true/error=null，面板底色 #19382B，输入面 #244638，与当前 Rhino 颜色相同。无模型调用。证据 artifacts/theme-ui-0227/{chat-browser-verified,chat-native,release-verified}.json。

八页均在 360/600 宽度做只读 WPF 布局捕获：标题／主次操作／折叠设置、材质查询、种植组合、属性、PSD 图层与后期入口；这些捕获不包含 WebView HWND，聊天另用真实 SDK CapturePreviewAsync 和浏览器截图验证。原生属性页普通物件的材质范围、Plants List 编辑／定位按钮和隔离编辑退出按钮通过。先前直接在 MCP 命令内调用 Refresh 的断言受到 InCommand 门控影响；改为真实 UI ticks 后验证，未绕过产品门控。

所有工具打开后 new → new → open，PID 25112 不变、八工具重绑定、案例恢复 70 对象且 Modified=false。原厂 HTTP 在文档切换时重置及短暂“文档已关闭”保留为延迟绑定观察，未重复发起 mutation；只读状态继续轮询。管理器确认先前 PID 26164 为 NormalExit。证据 native-layouts.json、native-actions-verified.json、lifecycle-verified.json、instances.json。未测试每种自定义系统配色、高对比度辅助模式或真实手绘硬件，未将这轮 UI 检查称为完整生图质量验证。

## 2026-11-11 · 0.22.8 PSD 通道与 Named View 工作台

完整 Build.ps1/Core 验证通过，新增 ExportChannelsValidation 覆盖隐藏图层／隐藏分组子层标志、兼容合成、三种分层等价、代表色、相机轴向深度、植物透明孔、跨块归一化和取消。最终原生布局改动由沙盒 build_test 编译，零警告／错误。

原厂 MCP 的正常入口最终在 B PID 19060 完成 600×450 六通道 PSD，20 个像素层，报告导出 9357 ms，端到端调用 9.812 秒。psd-tools 独立解码确认顶到底：植物、Shadow、材质、Arctic、深度图、材质颜色；后两项隐藏且保留数据，深度 256 灰阶覆盖 0–255。九个实际分层变体：材质代表色 8 材质／60 物件／1 全合并，图层色 11 颜色／60 物件／1 全合并，贴图 8 材质／60 物件／1 全合并；每组不同分层的兼容合成像素完全一致。证据 artifacts/export-0228/{supported-final-report,supported-final-psd-verified,variants-verified}.json。

原生创建、原位改名、外部改名同步、重名空名拒绝、尺寸与图层深复制、两级折叠隔离通过。自定义 Undo 实测创建和改名往返，重做新建的 SDK ID 改变后仍保留尺寸与后续改名记录。证据 names-fold-verified.json、undo-verified.json、ui-actions-verified.json。

所有八工具实际打开后 new → new → open，PID 19060 不变，八工具无错误重绑定，70 对象／Modified=false；最终原始 Hillside-UX-Audit.3dm 已恢复、PSD 页选中。首次生命周期脚本只分组打开但未逐页实例化，因只有两个实际工具未满足八工具断言；补齐真实逐页打开后通过，未将首次失败算成产品崩溃。最终额外打开原案例后的短暂“文档已关闭”也保留，随后只读确认并打开成功。证据 lifecycle-verified.json、final-case.json。

两条额外测试路径发生未确认退出：早期 ZBufferCapture 探针，以及末期直接构造未挂到 Rhino 容器的离屏 ExportPanel。没有用户关闭操作；管理器缺少完整退出码／转储，不能断言具体原生根因。产品深度不使用 ZBufferCapture，停止未挂载面板／WPF live-root 截图探针，恢复 B 后正常 MCP 导出和文档生命周期均通过。保留 offscreen-probe-exit.json 等证据，不宣称全部原生异常已根治。布局捕获受宿主裁剪影响，不作为所有 DPI／主题的完整视觉 QA；没有新增 4K/8K 深度性能测试。

## 2026-11-11 · 0.22.9 季节素材与预览交互

完整 Build.ps1（production-build.log）零警告／错误，全部既有 Core 回归及 SeasonalValidation 通过：一素材多季节引用、缺失／固定季节、复用图像尺寸及锚点、过期提交拒绝、ZIP 往返、水平平面与角度校验。正式实现和限制见 Seasons.md。

最终 B PID 56416、原厂 MCP 实测：18 个真实位图眼睛按钮、隐藏／显示往返、原生设置 Dialog 打开／关闭；默认新视图 Rendered。15 株切换平面，地面锚点不变、displayPosition 按实际树高抬升、heightMeters 不变、orientation=plan；夏冬材质在 Rhino 实际切换一项，原有纹理重复矩阵和全部对象 Geometry.DataCRC 不变，切回夏季恢复。透明裁片规范化独立验证宽度 8 m、基部锚点 .5。证据 final-check-{ui,native,final}.json。

600×450 默认六通道输出两个 PSD（春夏秋合并／冬季单独），每个 20 像素层，depth/color 隐藏标志及数据经 psd-tools 解码确认；只导植物的正俯视使用同一平面图，四季合成一个文件。季节随机缓存准备后，植物／材质／阴影／深度／颜色通道的夏季像素与先前一致。Rhino 自带 Arctic 捕获跨进程出现像素变化（最终 104266 像素），因此不宣称整个兼容合成跨实例逐像素一致。原先对全合成的断言因此失败，拆分通道后才确认自有通道的稳定性。证据 release-psd-report.json、release-psd-verified.json、top-release-verified.json。

真实模型调用：已有已核实 Tamarindus indica 立面作为参考，生成 1 张新透明平面 PNG，实际图片和 fresh-path 校验留存。AI 判断无霜正常供水气候下不需要温带落叶／雪景，四季八槽共用原立面及新平面两张文件；继续补齐已完整素材没有新模型调用。冬季比较图使用明确的合成测试图片，不冒充真实冬季生成结果。未验证所有物种的季节准确性、所有八张不同图的连续生成质量或 4K／8K 四季性能。

最终 new → new → open 同 PID、八工具无错误重绑定，原案例恢复 70 对象／Modified=false；切库前填充旧缓存再切回原库，15 株继续显示且回到无平面旧素材的 elevation，验证缓存按 Root+ID 隔离。复制案例和原 3dm SHA 相等，原素材库及偏好已恢复，临时季节图片只在 artifacts/seasons-0229/library。证据 lifecycle-verified.json、restored.json。

保留测试修正：首个 fixture GUID 拼写／内部方法不可直接调用、关闭 Dialog 时枚举集合被修改、重名输出自动 001 导致严格文件名断言失败、布局尚忙时导出被正确拒绝、Open 后原厂连接短暂重置。均未将失败算作通过；最终分步骤等待 UI ticks、只读确认再继续，不盲目重发变更。一次同时启动管理器编译和 Build.ps1 造成中间 ref DLL 冲突，已串行重跑通过。没有新增未确认 Rhino 退出，未使用用户鼠标或离屏构造面板探针。

## 2026-11-11 · 0.22.9 案例缺少平面素材的收尾修正

用户实际视口为平行投影、俯视 85.806°、auto 模式、planAngle=75°，但原素材库 Betula nigra seasonal.variants 为空，15 株均走缺图立面回退。上轮隔离测试成功不能代表恢复原库后的案例已具备平面图；这是示例准备遗漏，并非阈值未触发。

通过原厂 MCP seasonal_start（fourSeasons=false）给原库该父素材补齐夏季平面；复用既有立面，不新增父素材、不调整模型布局。真实 AI PNG 完成并经透明裁片规范化入库。最终同 PID 56416，15/15 orientation=plan，地面 position、heightMeters、相机方向逐项与调用前相同，Modified=false。原生当前视口 CaptureToBitmap 目视确认树冠平面。证据 artifacts/plan-followup-0229/{inspection,job,status,before,verified}.json 与 current-plan-view.png。本次更新的是该正式素材记录的季节图片，无代码升级、无 Rhino 重启、未使用鼠标。

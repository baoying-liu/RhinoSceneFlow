# SceneFlow · 20 秒动态试片 v01

用途：验证大画面、短标题、音乐卡点、图像运镜与 PSD 分层透视是否符合宣传片方向。不是完整教程或最终宣传片。

- 视频：`out/promo-sample-v01/SceneFlow-Promo-Sample-v01.mp4`
- 观看页：`out/promo-sample-v01/watch.html`
- 规格：1920 × 1080，30 fps，600 帧，H.264 / yuv420p，AAC 音频。
- Remotion：`SceneFlow-Promo-Sample-v01`；源文件 `src/PromoSample.tsx`。
- 配乐：`public/audio/sceneflow-pulse-120.wav`，20 秒，120 BPM，48 kHz 双声道。
- 配乐源程序：`production/make-promo-score.py`；固定随机种子，原创合成鼓、贝斯、和弦、琶音及过渡音效，无外部采样或第三方曲目，不含声音复刻。

## 节拍设计

每拍 0.5 秒，对应 15 帧。每两拍或四拍改变视觉，主要转场统一落在整拍。

| 时间 | 帧 | 画面 | 音乐对应 |
| --- | --- | --- | --- |
| 00:00–00:04 | 0–119 | 建筑局部快速拉开；Make it real. | 稀疏起势，标题进入鼓点 |
| 00:04–00:08 | 120–239 | 白膜、材质、带植物图与细化结果匹配切换 | 每两拍一次画面切换 |
| 00:08–00:11 | 240–329 | 材质底图上植物按区域显现，镜头横移 | 植物显现分两段落拍 |
| 00:11–00:15 | 330–449 | 实际 PSD 通道由叠合向外分离；概念图层面板逐拍强调 | 切场转音，逐拍图层高亮 |
| 00:15–00:19 | 450–569 | 源图与既有 AI 结果对齐位置擦除切换，镜头推进 | 节拍加强、转音衔接 |
| 00:19–00:20 | 570–599 | SceneFlow 品牌落点 | 低频落点与短尾音 |

## 真实性与当前限制

素材继承关键帧 v01 的来源记录。图像来自既有模型与 AI 案例，没有在本轮重新生成。源图与较晚 AI 输出存在几何差异，不能把擦除转场当作精确几何对比。

植物显现用实际透明植物通道表现，不是实时种植录屏。概念编辑器用来说明 PSD 图层结构，不是 Photoshop 联动演示。本轮没有新的材质随机参数、大小调整或四季操作录屏，也没有莫奈/星空等新风格，不能据此声称这些段落已制作完成。正式片需补拍真实操作与真实多风格结果。

当前运镜使用图像推拉、平移与 PSD 平面透视。真实建筑绕飞必须另从 Rhino 拍摄或模型渲染，不能靠图片旋转替代。完整宣传片的后续重点是增加这些空间镜头与风格结果，而不是继续叠加文字。

## 验证与重新导出

图像与音轨检查见同目录 `validation.json`。合成配乐的峰值/RMS 记录见 `score.json`，RMS 不等于 LUFS。

在 `media/tutorial-en` 运行：

```powershell
# 使用本机已有 numpy 的 Python 环境执行
python production/make-promo-score.py
npm run lint
npx remotion render SceneFlow-Promo-Sample-v01 out/promo-sample-v01/SceneFlow-Promo-Sample-v01.mp4 --codec=h264 --crf=18 --pixel-format=yuv420p --concurrency=3
```

????????? HTTP ??????????????`production/serve-preview.py`???? `http://127.0.0.1:3149/out/promo-sample-v01/watch.html`??????????? 1?9?12.8?19.3 ?????????????????????????????????????????????????

????????? Arctic ???????? 1200 ? 900 PSD ???????????????????????? `channel-manifest.json`?

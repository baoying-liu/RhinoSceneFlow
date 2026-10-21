# v0.2.1 复杂曲面验收

2026-10-21，使用沙盒 B、原厂 Rhino-MCP-Platform；管理 MCP 19540，实际 Rhino MCP 22801，最终测试 PID 33084。全程通过 MCP 与文件检查，没有鼠标操作，也没有部署到正式 Rhino。

## 发现和修复

v0.2.0 使用 `MeshingParameters.Default`。测试中的双线性马鞍形曲面被 Rhino 生成为 4 顶点、1 个非平面四边形；拆成两个平面三角形后，会改变曲面及透视轮廓。精确曲面求交检查发现了 2 个离边界足够远的错误样点。

v0.2.1 对 Brep、曲面和挤出体统一使用 QualityRenderMesh，初始采样网格最少 64 格并允许细化；真正的平面仍允许简化。原始 Mesh 和 SubD 的处理不变。Release 编译和原有核心回归通过。

## 实际形体

两个真实球体 Brep、双曲抛物面（马鞍形）、单叶双曲面、圆环 Brep、带内环裁剪的平面 Brep、底板 Mesh，共 7 个对象、6 种颜色。

单叶双曲面由两个半径 3、相差 120° 参数相位的圆构造精确直纹 NURBS 曲面；腰部半径数值验证为 1.5，未用采样网格冒充双曲面。

## 结果

| 视图 | 宽度 | 图层数 | 三角形数 | 导出耗时 |
| --- | --- | --- | --- | --- |
| 俯视 | 1024 px | 6 | 61,762 | 647 ms |
| 透视 | 1024 px | 6 | 61,762 | 406 ms |
| 低视角透视 | 1024 px | 6 | 61,762 | 205 ms |
| 低视角细节 | 2048 px | 6 | 61,762 | 560 ms |

- 共 3,396 个稳定样点，与 Rhino 原生 CurveBrep 精确求交得到的可见颜色完全一致。样点包括各形体、地板和透明背景；不把边界附近的网格近似差异当作内部遮挡错误。
- 独立 psd-tools 读取全部图层和 RGBA，图层重新合成与 PSD 合成预览的最大预乘 RGBA 差异小于 1.78/255。
- 圆环孔洞、裁剪平面内孔、单叶双曲面的开放中心在俯视图中正确显示下方地板。
- 球体俯视轮廓覆盖面积与理论圆的误差为 0.0296%。覆盖率从合成图与已知底板颜色反解，未把用于无缝合成的条件图层 alpha 当作几何覆盖率。
- 导出本身没有改变文档 Modified、对象数量、图层属性、选择、显示模式或相机。

求交参考来自原始 NURBS/Brep，而不是插件的三角形。使用 CurveBrep 而非 RayShoot，因为后者在当前 Rhino API 中忽略 Brep 裁剪环。当前安装版 GetFrustumLine 的平行视图线段方向与文档说明不同，参考脚本按相机距离显式校准近远端，避免反向求遮挡。

输出文件：

- `artifacts/rhino-B/complex/Complex-Surfaces.3dm`
- `artifacts/exports/complex-5b98a876-top.psd`
- `artifacts/exports/complex-5b98a876-perspective.psd`
- `artifacts/exports/complex-5b98a876-low-angle.psd`
- `artifacts/exports/complex-5b98a876-detail-2048.psd`
- `artifacts/rhino-B/complex/report.json`、`verified.json`、各视图 PSD 解码预览。

复现：在专用 B 测试文档运行 `scripts/Test-ComplexRhino.py`，再执行 `artifacts/verify-env/Scripts/python.exe scripts/Verify-ComplexPsd.py`。脚本只允许空文档或本测试的标记对象，避免覆盖用户模型。测试模型留在 B 通道，可手动检查。

仍是颜色分层导出，没有光照明暗。曲面网格仍是近似，质量提高会增加三角形数量；以上结果不能代表大量复杂曲面或超大场景的性能。未打开 Photoshop 应用，也未在本轮测试 SubD、块实例或大坐标。

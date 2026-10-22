# v0.5：Named View 导出面板

命令：`RhinoSceneFlowPanel`。使用 Rhino 自带 Eto 窗口和 ImageView 图片预览，同一文档重复执行命令会激活已有窗口。面板绑定打开时的文档，关闭文档会关闭面板并取消运行中的任务。

## 使用

1. 在 Rhino 中保存 Named Views，然后执行命令打开面板。
2. 点击“刷新 Named Views”读取新增、修改、删除后的列表；勾选需要导出的行。
3. 选中一行，单独设置宽、高。宽高各为 64–8192 像素，总像素不超过 800 万。
4. 选择着色、渲染、极地等当前 Rhino 提供的显示模式，点击“刷新预览”。右侧显示保存相机的静态预览，按输出画幅显示；修改模型后点击刷新。
5. 勾选材质/图层色、阴影中的一个或两个通道，选择输出文件夹，点击“批量导出 PSD”。

每个 Named View 输出一个同名 PSD。两个通道都选中时，PSD 包含各图层颜色的像素层和上方的独立 `Shadow` 层。只选一个通道时不加入另一通道。选中的阴影通道即使为空，也保留透明的 Shadow 层。

当前“材质 / 图层色”沿用已有的 Layer.Color 分层，尚不是纹理材质或渲染画面的导出。显示模式用于预览，不改变这两个导出通道的内容。

输出宽高变化通过 Rhino 原生视锥宽高比处理，保持相机投影而不拉伸几何；画幅变化可能改变裁切。每个视图的尺寸、勾选状态和预览模式在本次面板会话内保留，刷新列表按 NamedViewId 保留已有设置；关闭重开目前使用默认尺寸。

## 重名规则

- 已有 `视图名.psd` 时，开始渲染前弹出“是否覆盖”：是 → 覆盖；否 → 使用 `视图名001.psd`；取消 → 中止整个预检，不写入文件。
- 若 001 已存在，依次寻找 002、003……，包括本批次已经预留的文件名。
- 非法文件名字符替换为下划线，处理 Windows 保留设备名、尾部点和空格。同一批次不同 Named View 清理后重名时自动编号，不相互覆盖。
- 文件先写临时文件，完成后原子替换；取消或失败不会留下半成品 PSD。取消导出保留已完成的文件，每个视图的结果列出在面板底部。

## 执行方式

UI 线程读取文档、Named View 和场景快照，使用独立的 `RhinoViewport()` 计算相机；后台任务只接触值类型、独立网格数据和自有 Brep 副本，负责阴影计算与 PSD 写入。进度按视图更新，取消按钮能在后台任务期间响应。

不要用 `new RhinoViewport(activeViewport)` 再设置 Size：Rhino 的该复制对象仍关联 ParentView，实测会改变主视图尺寸。导出使用完全独立的视口，同时显式使用真实模型视口的可见性过滤。v0.5.1 移除会遗留浮动 Custom view 窗口的 ViewportControl。预览在暂停重绘期间借用现有模型视图捕获图像，并在 finally 中恢复相机、显示模式、网格、坐标轴及 Modified；不调整主视图尺寸，不创建任何 RhinoView。

所有通道使用相同细分精度和相机，避免勾选阴影改变材质通道轮廓。阴影采用阴影体加原始曲面复核方案。v0.5.1 默认包含背光面和自身遮挡，仅计算太阳直射光，不计算反射、间接光、AO 或软阴影；极地/渲染预览的光照效果不代表导出通道。合并图层时保留每个通道独立 alpha，PSD 合成预览与普通图层混合一致。

## 原厂 MCP 接入

仍通过已安装的 Rhino-MCP-Platform `run_python` 调用 `RhinoSceneFlow.Plugin.McpApi.Execute(JSON)`，没有增加服务、端口或顶层工具。接口版本仍为 1。

| operation | 参数 | 返回 |
| --- | --- | --- |
| `open_panel` | `document` | 打开/激活面板，返回面板状态 |
| `panel_status` | `document` | 面板状态或 `open:false` |
| `named_views` | `document` | Named View 的 id、名称、默认宽高 |
| `export_named_views` | `document`, `directory`, `views:[{viewId,width,height}]` | 每个视图的文件、尺寸、图层数、耗时及错误 |

批量 API 可选 `channels:["material","shadow"]`，默认两个都选；可选 `collision:"number"`（默认）、`"overwrite"` 或 `"cancel"`。API 不弹覆盖窗口，默认安全编号；只有显式 overwrite 才覆盖。面板始终按上述 Yes/No/Cancel 询问。

```python
request = {
    'apiVersion': 1, 'operation': 'export_named_views',
    'document': int(__rhino_doc__.RuntimeSerialNumber),
    'directory': r'C:\Exports',
    'views': [{'viewId': '从 named_views 取得的 GUID', 'width': 1600, 'height': 1000}],
    'channels': ['material', 'shadow'], 'collision': 'number'
}
print(McpApi.Execute(json.dumps(request)))
```

该 API 同步执行；面板按钮使用后台执行版本。参数预检失败时整体拒绝，渲染中某个视图失败则记录该项错误并继续其余视图。面板尺寸等设置不自动写入 .3dm。

## 验证

仅在固定沙盒 B（管理 MCP 19540）测试；生成文件在 `artifacts/rhino-B/panel/`。没有发布正式 Rhino，没有使用鼠标，没有打开 Photoshop。

验证覆盖 320×200、384×192、240×240 三种画幅；材质单通道、阴影单通道、合并通道；中文文件名；已有原名及 001 时使用 002，再次导出使用 003；显式覆盖及取消预检；无效尺寸和无通道拒绝；文档、主视图、图层和选择保持。

直接操作真实 Eto 控件验证单独改尺寸、刷新保留尺寸及 Shaded、Rendered、Arctic 预览。原生预览截图通过对应视口绘制生成。WPF 布局截图不能包含原生视口的 HWND 内容，不能据此把空白截图区域当作预览失败。

实际新增、删除、重命名 Named View 后刷新列表亦通过，重命名保持稳定 id 和已编辑的输出尺寸；测试后恢复原命名视图列表，证据为 `refresh-report.json`。

独立 psd-tools 检查真实文件的尺寸、通道图层、单色阴影及图层重新合成。核心验证增加多通道叠加、透明阴影层和重名预留测试。

最终 v0.5.0 在 B 的 PID 249608 加载，管理任务 `44278831ef4f4237b169e80e185e9fb7` 成功，部署 `20261022-191804-c07133e5b33c442695602468510eb4e8`；原厂 Platform 22801。7 个真实 PSD 解码通过，最大预乘 RGBA 重合成差约 1.97/255。材质单通道与合并文件中相应色层逐像素一致，阴影单通道与合并阴影层亦一致。

实际面板后台导出 352×224 文件约 4.8 秒；任务期间 UI 定时器响应 66 次。通过真正的 Eto 取消按钮取消 2048 导出，未留下 PSD 或临时文件。证据为 `report.json`、`verified.json`、`async-report.json`、`cancel-report.json` 及三种原生模式 PNG。覆盖策略通过核心测试和 API 验证；自动化没有用鼠标点击原生覆盖询问弹窗。

```powershell
.\scripts\Build.ps1
python scripts/Rhino-Mcp.py run_python scripts/Test-ExportPanel.py
python scripts/Rhino-Mcp.py run_python scripts/Test-ExportPanelUi.py
python scripts/Rhino-Mcp.py run_python scripts/Test-ExportPanelRefresh.py
artifacts/verify-env/Scripts/python.exe scripts/Verify-ExportPanel.py
python scripts/Rhino-Mcp.py run_python scripts/Test-ExportPanelAsync.py
# 让 Rhino UI 调度器继续运行，再检查：
python scripts/Rhino-Mcp.py run_python scripts/Check-ExportPanelAsync.py
python scripts/Rhino-Mcp.py run_python scripts/Test-ExportPanelCancel.py
python scripts/Rhino-Mcp.py run_python scripts/Check-ExportPanelCancel.py
```

真实 Rhino 测试只接受专用研究标签场景，生成自身前缀的 Named Views；空文档从此前的研究测试 3DM 加载，不替换用户模型。异步检查未完成时可稍后再次查询，不要在 Rhino UI 线程同步等待任务结束。

布局、关联裁剪平面、透明材质/植物 alpha、隐式地面及渲染器效果仍不在 PSD 导出范围；原生预览可能显示这些内容，因此不能把预览当作所选通道的逐像素结果。阴影准确性和性能边界仍见 [Shadow-Accuracy.md](Shadow-Accuracy.md)。

# ChatKit and xatlas (v0.11)

`RhinoSceneFlowMaterials` opens the native Eto panel. The first tab contains the official OpenAI ChatKit web component hosted in WPF WebView2. **快捷生成** retains the native single-request form. The bottom Apply scope still reads the current Rhino selection at each click.

The ChatKit Python SDK implements conversation storage, attachments and SSE. A random-token loopback HTTP endpoint serves this UI only; it is **not an MCP endpoint**. The SDK delegates turns over stdio to the plugin, which runs local Codex using its existing ChatGPT login. No OpenAI API key, Agent Builder workflow, embedded ChatGPT website or extra MCP server is required. Ordinary discussion returns text; explicit requests to create or revise a material invoke image generation. New images are verified against that invocation's Codex thread and imported into the material library. Previous generated images and uploaded references inform revisions. This is one local Codex invocation per turn with recent conversation supplied as context, not a resumed Codex CLI session.

Run `powershell -ExecutionPolicy Bypass -File scripts/Setup-ChatKit.ps1` once. Python 3.10+ and the WebView2 Evergreen runtime are required. The official ChatKit frontend is loaded from OpenAI's CDN and needs network access. Missing dependencies/network errors are displayed explicitly; the native tab remains available. Runtime and conversations reside under `%LOCALAPPDATA%/RhinoSceneFlow`. Closing the panel stops its owned UI backend and pending chat turn. No user browser or mouse automation is used.

## Complex UVs

Select objects and run **`RhinoSceneFlowUnwrap`**, or choose **xatlas 复杂曲面展开** under **尺寸与铺贴**, then click **计算 / 更新真实世界 UV**. The Apply button performs the selected xatlas preparation before applying. Valid existing mappings are reused on subsequent material changes; stale xatlas mappings in this panel are recomputed before Apply.

The pinned MIT xatlas C++ sources build as `SceneFlow.UvWorker.exe`. The plugin snapshots an owned mesh on Rhino's UI thread, computes charts in a separate hidden process, then commits a native custom mesh mapping back on the UI thread. The original Mesh/Brep/SubD geometry is retained. Jobs can be cancelled. Changes to source geometry, units or mapping during computation reject the stale result. A batch commit restores captured mappings/attributes if committing fails. Native undo records the successful commit.

UV units represent meters after global surface-area calibration. Asset physical dimensions stay in the material's texture repeat, so changing a 1 m asset to a 600 × 300 mm asset does not require unwrapping again. Curved, nondevelopable surfaces still require seams and have local distortion. The job reports chart count and median/95th/max **length stretch factors**; 1.20 means up to 20% expansion or reciprocal compression. These are unweighted triangle statistics, not a guarantee of exact local scale. The custom mapping mesh is also used directly by the textured PSD channel to retain seam UVs. Native NURBS display uses Rhino's custom-mesh projection; its visual seam fidelity must be assessed separately from the export mesh.

The high-density Rhino fixture exposed rare xatlas boundary faces with extreme compression. Faces over a 2× length-distortion threshold are separated into metric triangle islands outside the existing atlas, followed by total-area calibration and recomputation of every triangle statistic. This adds seams; it does not blur images, change source geometry or suppress bad samples. More than approximately 2% such faces rejects the result. `repairedTriangles` and `rawStretchMax` retain the original failure evidence (null raw maximum denotes an infinite/collapsed solver result). Baseline evidence remains under artifacts.

Blocks and per-face multi-material Breps are not newly supported. Rotation/offset controls currently belong to the primitive mapping modes; xatlas defines its own island layout. A changed or rescaled xatlas object must be unwrapped again. Legacy synchronous `material_remap` reports the need to use the asynchronous xatlas operation.

## Platform automation

All automation remains `RhinoSceneFlow.Plugin.McpApi.Execute(JSON)` through the installed Rhino-MCP-Platform on the UI thread:

```json
{"apiVersion":1,"operation":"material_unwrap_start","document":1,"objects":["OBJECT-GUID"]}
{"apiVersion":1,"operation":"material_unwrap_status","jobId":"JOB-GUID"}
{"apiVersion":1,"operation":"material_unwrap_cancel","jobId":"JOB-GUID"}
{"apiVersion":1,"operation":"material_chat_start","conversation":"USER: 生成浅灰混凝土材质","widthMeters":1,"heightMeters":1,"referenceImages":[]}
{"apiVersion":1,"operation":"material_chat_status","jobId":"JOB-GUID"}
{"apiVersion":1,"operation":"material_chat_cancel","jobId":"JOB-GUID"}
```

The chat API returns the actual material ID/image path only after successful generation and import. Text-only replies return no material. Unwrap reports immutable source correspondence, triangle counts, charts, area and stretch. Poll jobs in later calls; never block Rhino's UI waiting for them. `material_apply` then reuses valid calibrated UVs. Existing `kind:texture` and `textureGrouping:material|object` PSD configurations work with the unwrapped mappings.

Build and validation: `scripts/Build.ps1` compiles the C++ worker, managed plugin and portable tests. `scripts/Test-ChatKitProtocol.py` exercises the real ChatKit SDK/SSE/SQLite with an explicit fixture agent (no image generation). `dotnet run --project tests/RhinoSceneFlow.Validation -c Release -- --chat-smoke` invokes real local Codex for a text-only reply. B integration uses `Test-XatlasRhino.py`, `Check-XatlasRhino.py`, `Probe-ChatKitRhino.py` and `Check-ChatKitRhino.py`. Receipts and test models are under ignored `artifacts`.

Official references: [custom ChatKit server](https://developers.openai.com/api/docs/guides/custom-chatkit), [ChatKit guide](https://developers.openai.com/api/docs/guides/chatkit), [xatlas upstream](https://github.com/jpcy/xatlas).

Native GPU validation in a fresh hidden sandbox requires an initialized visible Rhino viewport. The final B test explicitly showed only its managed instance through MCP and re-exported display layers after initialization; it did not use mouse input.

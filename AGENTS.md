# RhinoSceneFlow development

- Product scope: AI assets → physical-scale materials → planting → view-layer export → postproduction. Current implemented slice is layer-RGB PSD export and Platform automation.
- Keep geometry/projection/PSD serialization in Core; Rhino SDK, commands, preferences and the public JSON API belong in Plugin. Commands and automation call ExportService.
- Depend on the user's installed Rhino-MCP-Platform. Do not start another MCP server, patch Platform private implementations, or edit Codex MCP configuration for this project.
- Automation entry point: `RhinoSceneFlow.Plugin.McpApi.Execute(JSON)` via Platform `run_python`. Update docs/MCP.md with API changes.
- Test only in RhinoDevSandbox channel B (`1cee488700ad42f59492743cc4a2a3fe`), management MCP 19540. Discover the actual Rhino MCP port from B's Monitor record and verify PID. Do not assume the launcher's selected UI tab is B.
- Prefer MCP and file-based PSD inspection; avoid taking the user's mouse. Use no save dialogs in automatic exports.
- Default B export directory is this project's `artifacts/exports`. Generated PSDs, models, receipts and previews stay under ignored artifacts. Never commit credentials.
- Build/package with scripts/Build.ps1. Validate real exports with scripts/Smoke-Rhino.py (requires a fresh empty B document) and scripts/Verify-RhinoPsd.py (independent psd-tools decoder).
- Manage test instance builds/restarts through the sandbox MCP. Retain failed/unknown exit evidence; do not force-kill instances or change another channel.
- No formal Rhino deployment is implied by sandbox test work. Preserve document geometry, attributes, selection, view and modified state during exports.
- Update docs/Validation.md and docs/Sandbox-B.md with actual evidence; distinguish independent file decoding from opening Photoshop itself.

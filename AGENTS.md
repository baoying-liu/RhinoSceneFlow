# RhinoSceneFlow development

## User Experience First

For every user-facing feature, prioritize usability, workflow efficiency,
discoverability, and consistency. Follow [the UX workflow](docs/UX-Workflow.md).
Scale the review and testing to the change; routine fixes do not need a design
ceremony or a new report.

Before implementation:

- Identify the primary user, their goal, and the existing entry point.
- For new workflows or substantial interaction changes, consider at least two
  interaction designs. Small fixes should follow established patterns.
- Prefer fewer unnecessary actions without hiding important functionality or
  making the workflow harder to understand.
- Reuse established UI patterns, terminology, and shortcuts. Check whether an
  existing control or setting can be reused instead of adding a duplicate.
- Identify likely mistakes, affected data, and recovery paths.

During implementation:

- Provide clear feedback for actions, task progress, and outcomes; never invent
  progress or imply that a saved draft is a completed result.
- Support undo for reversible editing operations. Distinguish undo, cancellation,
  restoring defaults, and image backups; state any recovery limitations honestly.
- Avoid unnecessary modal dialogs. Prefer inline editing and contextual controls.
- Preserve user context, selection, focus, scroll position, and viewport state
  unless changing them is the explicit purpose of the action.
- Keep frequent actions fast and accessible; disclose advanced settings on demand.
- Support appropriate keyboard shortcuts without capturing text editing, IME,
  or established host shortcuts unintentionally.
- Never sacrifice reliability, source integrity, or recoverability for appearance.

After implementation:

- Review the complete affected user interaction flow, not just the new control.
- Check confusing labels, duplicate settings, hidden functionality, and unnecessary
  navigation or repeated selection.
- Check applicable empty, loading, error, and success states, plus locked, pending,
  and stale-input states when the feature uses them.
- Identify repetitive actions that could be automated with predictable defaults.
- Test normal use, common mistakes, recovery, and context preservation. Report
  actual evidence and limitations; do not label untested behavior as verified.

When a significantly better UX is possible, proactively recommend it with a short
rationale. Implement improvements within the authorized scope. Do not redesign
unrelated UI without authorization, and do not add a new approval step to routine
work already authorized by the user.

## Product and interaction consistency

- Scope: AI assets -> physical-scale materials -> planting -> view-layer PSD
  export -> postproduction. Core owns portable geometry/projection/serialization;
  Plugin owns Rhino SDK, native Eto panels, commands, and public automation.
- Respect native Rhino behavior in docked tools and established canvas behavior
  in the Web workbench. Share meanings across them without forcing identical UI.
- List, canvas, PhotoCraft, and inspectors operate on shared stable identities.
  Reuse the existing owner, state, selection and persistence models.
- Keep visibility, AI participation, content locking, saved-but-pending edits,
  stale inputs, and completed results distinct. Use text/icons as well as color.
- Keep original inputs and result ancestry traceable. Preserve source files,
  immutable versions, user descriptions, asset names, and Latin plant names.
  UI language changes must not rewrite user data.

## Required technical contracts

Before modifying an affected subsystem, read its section of
[Development-Contracts.md](docs/Development-Contracts.md) and the linked feature
specifications/test harnesses. All existing implementation constraints, required
regressions, known failures and historical evidence remain there. Read multiple
sections for cross-cutting changes; do not treat moving a rule as relaxing it.

- Studio, canvas, AI tasks, PhotoCraft: Studio and PhotoCraft.
- Planting, group editing, selection and display: Planting, selection and display.
- Library, materials, Eto lifecycle and document changes: Materials, shared
  library and document lifecycle; also the UV/material generation section.
- Rendering, shadows and PSD export: Shadows and accuracy; Named Views, panels
  and PSD export; texture-export constraints in the UV/material section.
- Any Rhino automation/build/deployment: Architecture, automation and sandbox
  boundaries. Preserve explicit limits and distinguish diagnostics from guarantees.

## Automation and delivery boundaries

- Use the installed original Rhino-MCP-Platform through
  RhinoSceneFlow.Plugin.McpApi.Execute(JSON), called by Platform run_python.
  Do not add an MCP listener, patch Platform internals, or edit Codex MCP config.
- Test only in RhinoDevSandbox B: office 1cee488700ad42f59492743cc4a2a3fe;
  home 0d327c4c84f644f089b73834ffd93cfe. Resolve the local catalog, require the
  known B ID, discover the Platform port from its monitor and verify the PID.
  Management MCP is 19540; the selected launcher tab does not identify the target.
- Manage sandbox builds/restarts through its MCP. No force-killing instances,
  changes to other channels, or implied production Rhino deployment.
- Prefer MCP, file inspection and isolated headless browser tests; avoid using
  the user's mouse. Preserve documents, source assets, credentials and existing
  work. Never print bearer tokens or authenticated launch URLs.
- Build/package code changes with scripts/Build.ps1 and run the regressions
  required by the affected contract. Match test scope to risk; documentation-only
  changes need document/link checks, not Rhino restarts or image generation.
- Keep generated files, receipts and test artifacts under ignored artifacts.
  Report changes, validation, and material limitations clearly. Update docs/MCP.md
  for API changes, and docs/Validation.md / docs/Sandbox-B.md for actual runtime
  validation/deployment. Never claim installation, visual QA or AI generation
  from a build, a synthetic fixture, or a status-only check.

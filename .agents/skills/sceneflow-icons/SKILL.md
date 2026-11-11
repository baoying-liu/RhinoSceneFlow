---
name: sceneflow-icons
description: Select, design and validate small toolbar, sidebar and action icons for RhinoSceneFlow's Rhino/Eto panels and Web Studio. Use for icon semantics, SVG sources, theme variants and PNG/ICO exports; not for general page layout, material textures or plant images.
---

# SceneFlow Icons

Produce legible icons with the same action meanings in Rhino and Web Studio.
Read [the project reference](references/sceneflow.md) for integration paths,
candidate mappings and tool versions before changing assets.

## Use the project visual language

- Locate RhinoSceneFlow in the current workspace by `RhinoSceneFlow.sln` and
  `AGENTS.md`; read the applicable UI contracts.
- Inventory the existing icon and callers first. Reuse the same symbol for the
  same action across surfaces; distinct actions should not share a glyph just
  because it is convenient.
- Prefer Lucide for new general action glyphs. Keep existing coloured workspace
  tiles as containers when extending that family. Do not migrate a whole UI to a
  different style during a single-icon task.
- UV, plant groups and PSD channels may need a simple custom vector in the same
  visual language. Avoid tiny text or several overlapping metaphors at 16px.

## Source and author vectors

- Use Better Icons CLI for discovery, e.g.
  `better-icons search tree --prefix lucide --json`. Do not run `setup` or add an
  MCP service for this workflow. On this Windows setup it is also available at
  `$env:LOCALAPPDATA/CodexTools/node-runtime/better-icons.cmd`.
- Parse the retrieved SVG and compare fill/stroke and geometry with its original
  family source. Better Icons is a discovery aid, not the artwork/licence authority.
- Keep a local, version-pinned SVG master with its source and licence. The checked
  Lucide revision is in the reference. Installed UI icons must work offline.
- Preserve intentional `fill="none"`, `currentColor`, viewBox and stroke rules.
  Do not globally inject fills or strip all fills. Read the concrete CLI 1.0.4
  conversion observation in the reference before using its SVG output.
- Use static vector geometry; prefer editing SVG/code-native assets over raster
  image generation for these small interface glyphs.

## Package for both surfaces

- Use a 24-unit Lucide-compatible master grid and its 2-unit stroke as a starting
  point. Make optical corrections only when small-size comparison demonstrates
  a need. Do not stretch aspect ratios or thicken every path blindly.
- Web: local inline SVG/React, `currentColor`, explicit display size. Icon-only
  buttons need a localized accessible name and tooltip; decorative SVG must not
  add a second spoken label.
- Rhino/Eto: transparent PNG/ICO resources at the sizes actually used. Check
  16/20/24/32px and include 48/64px when the existing ICO/RUI pipeline needs them.
  An SVG preview alone does not prove Rhino can display the packaged resource.
- Normal, selected, disabled and toggled states follow host/theme colours.
  Distinguish Show/Hide with eye/eye-off shapes rather than colour alone or font
  symbols. Keep focus and pressed feedback in the existing button control.

## Verify the affected interaction

- Render the family together at actual small sizes on light and dark backgrounds.
  Inspect alignment, gaps, stroke weight, silhouettes and confusing pairs; a large
  isolated SVG is insufficient.
- Verify native sizes/transparency and browser accessible names where changed.
  Use existing headless browser/MCP harnesses, preserve selection/view and follow
  repository sandbox rules for any B test.
- Report which assets changed and which checks actually ran. A tool install or
  contact sheet is not a deployed Rhino UI or a completed icon migration.

The repository's `.agents/skills/sceneflow-icons` is the canonical portable copy.
The user-installed copy enables discovery outside that repository; keep it in
sync when editing this skill.

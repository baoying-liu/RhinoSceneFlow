# Project integration and source baseline

These mappings are starting candidates, not current UI replacement claims.
Preserve semantic identities, command names and panel GUIDs.

## Integration points (repository-relative)

- `scripts/Generate-WorkspaceIcons.py`: current deterministic Pillow artwork and
  16/24/32/48/64px ICO export into `src/RhinoSceneFlow.Plugin/Resources`.
- `scripts/Generate-Toolbar.py`: current RUI generation from those resources.
- `src/RhinoSceneFlow.Plugin/WorkspacePanels.cs`: panel icons/navigation.
- `src/RhinoSceneFlow.Plugin/WorkspaceAppearance.cs`: native text/theme handling.
- `web/postproduction/src`: React/inline SVG controls and theme styles.
- Existing live RUI caches may contain user customization; a source RUI change
  does not prove an already-loaded toolbar changed. Follow deployment contracts.

For an SVG migration, adapt the development export pipeline to consume pinned
masters and verify its output. The current Pillow drawing script is NOT an SVG
rasterizer. Do not add a Rhino runtime SVG dependency just to build resources.
Trials/contact sheets belong under ignored `artifacts/`; accepted masters and
licences belong in maintained project resources.

## Candidate semantic map

| Resource / meaning | Lucide candidate | Distinction |
|---|---|---|
| Workspace / dock tools | `panels-top-left` | UI containers, not model groups |
| Materials / AI asset conversation | `message-square-more` | Conversation, not library |
| Library / material library | `swatch-book` | Materials, not plant groups |
| Uv / physical-scale mapping | `grid-3x3` | Mapping; explain physical size in label |
| Planting / plant library and placement | `trees` | Species/assets and planting |
| PlantsList / existing groups | `list-tree` | Existing groups/hierarchy |
| Properties / current selection | `sliders-horizontal` | Selection-specific controls |
| Export / layered PSD output | `file-output` | Export, distinct from layer controls |
| PostProduction / AI Web Studio | `image` | Image workbench, not animation |
| Settings / global preferences | `settings` | Global, not selection properties |

Common actions: `eye` / `eye-off`, `refresh-cw`, `copy`, `clipboard-paste`.
All filenames above were retrieved from the pinned source. Retain labels/tooltips
for ambiguous specialised tools. Final choice requires small-size visual review.

## Checked toolchain and licences

- CLI package: npm `better-icons@1.0.4`, repository `better-auth/better-icons`.
  Its checked `--version` command reports hard-coded `1.0.0`; use the installed
  package.json/npm package version for this toolchain receipt.
- Upstream Skill revision: `033316ecb8f4982235af4111a2257e80231f5ab1`, path `skills/SKILL.md`.
- Lucide vector revision: `03eae6069edfc373673bd05d723491f05ba936e3`.
- Canonical SVG URL pattern:
  `https://raw.githubusercontent.com/lucide-icons/lucide/<revision>/icons/<name>.svg`.
- Better Icons: MIT. Lucide: ISC, with Feather-derived MIT artwork. Preserve the
  applicable original notices with distributed assets. Other Iconify families
  have their own licences.
- Notices: https://github.com/better-auth/better-icons/blob/main/LICENSE and
  https://lucide.dev/license.

### Observed SVG conversion difference (1.0.4)

The checked `better-icons get lucide:trees --json` response inserts explicit
`fill="currentColor"` on paths. Canonical Lucide uses inherited `fill="none"`;
raw Iconify JSON retains unfilled paths too. Blindly accepting this conversion
can turn an outline into a filled shape. Use the canonical family SVG as master
after discovery. Do not patch the installed upstream tool or apply a universal
fill-replacement workaround to other icon families.

Setup receipts and small-size trials: `artifacts/icon-skill-setup/`. These are
development checks; no application icons were replaced during Skill setup.

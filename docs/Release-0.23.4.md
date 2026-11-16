# SceneFlow 0.23.4 — public preview

Emissive materials now connect Rhino materials, layered PSD export and AI
postproduction guidance.

- Set emission color and artistic intensity in Materials or Properties. Explicit
  emissive AI-material requests can return emission metadata alongside base color.
- Add an Emission PSD channel, merged into one layer or separated by material or
  object inside a folder. Hard Light is the default blend mode.
- Bloom is enabled by default and can be disabled per channel. Opaque scene
  geometry occludes emission sources; emission masks preserve transparent black areas.
- Web Studio recognizes emission as Reference and can supply a separate aligned
  guide to AI generation. PSD Hard Light and Screen are accepted during preflight
  and PhotoCraft reference return.
- Fixed installer path comparison that could mistake a managed SceneFlow install
  for a manual registration when slash styles differed. Manual/Yak copies still
  require explicit removal; this does not bypass the ownership check.

See [Emission workflow](Emission.md) for controls and limitations. Intensity is not
lumens; PSD bloom is a screen-space effect, not GI or physical light transport.
The 8-bit pass tone-maps HDR emission. Transparent transmission and block/per-face
material export are not supported by this channel.

## Download and install

Download **SceneFlow-Setup-0.23.4-win-x64.exe** and **SHA256SUMS.txt** from this
release. Save work and close standard Rhino before installation. Start Rhino 8
and run **RhinoSceneFlow** afterward. See [Getting Started](Getting-Started.md).
Libraries and boards are retained. Development B is independently registered.

This is an **unsigned public preview**, not a signed stable release. Windows may
warn about an unknown publisher. Automatic installation of updates remains
disabled pending trusted signing. Legacy/manual registrations must be removed
before the first managed install. Clean-machine installation, repair, uninstall
and upgrade acceptance remain outstanding; package inspection does not replace
those checks.

## Validation and known limits

The full application build and core validations passed. B-channel exports were
independently decoded for grouping, visibility, Hard Light and bloom. Real local
browser tests verified emission guide participation and preflight; existing
PhotoCraft reference/guide round trips passed. No real image generation was run
for this feature, so AI lighting fidelity is not yet visually validated.
Script-level native Undo/Redo probes were inconclusive; interactive emission-edit
Undo/Redo still needs acceptance testing. Keep a saved copy before editing.

Image-model calls use the user's own account allowance or applicable credits.

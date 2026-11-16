# Emissive materials

SceneFlow 0.23.4 development build adds a connected emission workflow.

- In **AI assets**, explicitly request an emissive material (for example, a warm
  LED panel). The image remains clean base color; the returned emission color
  and artistic intensity are saved separately in the material asset.
- **Materials → appearance → Emission** edits library defaults for the next
  application. **Properties → material settings → Emission** edits the current
  document, using the existing material/layer/object scope and sharing isolation.
- In a Named View's **PSD layers**, add **Channel · Emission**. New default
  stacks include it. Untouched older defaults are upgraded; custom stacks retain
  their configuration. Initial visibility and export enable remain separate.
- Emission uses **Hard Light** by default, with standard opacity/blend controls.
  Choose **all** for one flattened emission layer, or **object/material** for
  layers inside an emission folder. Bloom defaults on and can be disabled in
  this channel. Separated output retains sources and a bloom subgroup.
- Export reads effective native PBR emission and optional grayscale emission
  maps; non-emissive geometry occludes the sources. Like the texture channel,
  this pass currently requires opaque materials; transparent transmission and
  block/per-face-material export remain unsupported and are rejected. Mapped emission uses the
  existing physical UV. Export never prepares or changes UV itself.
- Web Studio identifies emission as **Reference only**. Visible layers
  participate by default. When enabled, an independently rendered, aligned
  emission guide is attached to whole-image generation, with instructions to
  retain source positions/colors and add plausible local light spill. Disabling
  participation removes the guide under the existing participation rules.

Intensity is an artistic multiplier, not lumens or lux. The 8-bit PSD pass
tone-maps HDR emission while preserving hue; it does not contain HDR values.
Bloom is a screen-space effect, not GI, reflection or light transport. Rhino
display modes may differ from path-traced output. AI guidance cannot guarantee
physical lighting accuracy or exact pixel/geometry preservation.

Validation: `EmissionValidation` (`--emission`), `scripts/Test-EmissionGuides.py`,
and B-only `scripts/Test-EmissionRhino.py`. Models, PSDs and failed probes remain
under ignored `artifacts/emission` and `artifacts/rhino-B/emission0234`.

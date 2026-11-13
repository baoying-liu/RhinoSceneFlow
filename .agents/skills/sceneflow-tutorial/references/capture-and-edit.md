# Capture and edit

## Sources and setup

Locate the current release, installation guide, existing case, capture scripts
and saved boards. Confirm actual installed versions/UI instead of presenting
historical production notes as current facts. Use a copied case and checkpoints.
Generated media belongs in ignored output/artifact paths or the user destination.

Download entry: https://github.com/baoying-liu/RhinoSceneFlow/releases . Verify the
current release/EXE when producing footage; `/latest` may omit preview releases.
Do not teach source ZIP installation or simulate trusted publisher approval.

Distinguish bundled original McNeel MCP from optional external agent setup.
Show current product environment/sign-in and connection settings; do not invent
a universal port or expose bearer-bearing URLs. Installation illustrations are
allowed by the current brief; label them and match the actual installer flow.

## Confirmed SceneFlow tutorial direction

For the current English, approximately 15-minute tutorial, the user accepted
the framing in `media/tutorial-en/out/tutorial-rhino-sample-v02/`. Preserve the
accepted cut; the acceptance covers visual direction, not narration fluency.

- Capture the existing test Rhino workspace with its real theme and colors.
  Keep SceneFlow set to follow Rhino; do not substitute an unthemed standalone
  Eto window, recolor screenshots, or impose a generic dark palette.
- Show the actual enabled tool icon rail/tabs and surrounding Rhino context
  first. Use the real option to expose the tool entries when needed; do not
  paint fictitious navigation onto the interface.
- On entering Rhino, establish the full workspace. Outline the operation
  panel and model viewport with two restrained frames, then smoothly carry
  those same regions into a split layout. This establishes where the enlarged
  content comes from. Keep this split across the Rhino teaching sequence;
  tool/section changes do not automatically trigger another pullback.
- Keep settings on the left and the model on the right. Split views serve
  readability; their widths may change with the teaching focus. Enlarge the
  relevant control only when the existing split cannot make it legible, then
  hold through the explanation/action. Do not zoom again when the split is
  sufficient. Returning to context is optional, for orientation rather than
  decoration. Avoid repeated enlarge/shrink pulses.
- Switch SceneFlow tools using the actual top dropdown, visibly demonstrating
  that entry point. The enabled icon rail remains context, not the primary
  navigation taught in this tutorial. The right viewport may switch between
  actual Rendered, Shaded or Arctic display modes to clarify the current point;
  name the switch and do not confuse it with changing materials or PSD passes.
- Crop actual viewport pixels tightly enough to show the model, while
  retaining useful margins. Clip source pixels explicitly: contain/letterbox
  fitting must not reveal neighboring toolbars in the spare space.
- Use genuine current controls for the main tutorial. An MCP-operated state
  sequence with an editorial cursor is an edited demonstration, not continuous
  mouse recording. Retain that provenance in the review page/manifest. Do not
  imply drag, hover, menu or click behavior that was not actually verified.

The existing source examples are `src/TutorialRhinoSampleV02.tsx` under
`media/tutorial-en/` and its ignored source assets. Reuse framing ideas, not
hard-coded window sizes, capture coordinates, PID, colors or old UI labels.
Record these anew for the current session. Restore temporary preferences and
case export settings after capture; do not overwrite the original case.

## Current fifteen-minute teaching sequence

Use the cue CSV's revised timings as a budget, not a reason to accelerate
speech. Prioritize one reproducible material creation and one plant creation
over an exhaustive tour of settings.

1. Show the public EXE download, installation and initial environment/AI check.
   Installer illustrations remain labelled; use the real interface afterward.
   Explain the original MCP connection separately from AI account authorization.
2. Enter the existing Rhino case as a clean white model with no planting.
   Show target selection, one material description, optional reference input,
   reuse-versus-generation feedback, completed asset and actual application.
   Explain object/layer scope and automatic physical UV preparation at the
   point they matter; use a measurable texture such as wood for scale checks.
3. In the same AI chat, create one plant, with actual identification/reuse/
   generation feedback. Explain transparent elevation/plan assets, choose a
   carrier, place/scatter it and show the few controls needed to reproduce it.
   Prioritize density, size range and seed; show avoidance input briefly when
   relevant. Do not spend the chapter generating multiple species or seasons.
4. Explicitly switch to a prepared, completed checkpoint of the SAME model to
   skip repeated application/planting, not to imply one click finishes the site.
   Use genuine Rhino camera motion to show Z-axis camera following, higher
   angles and plan-image switching. Show the real settings entry and governing
   angle/height controls. Verify plan assets exist before filming; do not
   substitute a rotated elevation image and call it a plan asset. A quick
   individual edit or season preview is secondary to these core demonstrations.
5. Keep export settings on the left. Open the newly exported layered PSD in
   actual PhotoCraft on the RIGHT, temporarily replacing the viewport region.
   Toggle the corresponding real PSD layers/groups as each channel is explained:
   plants and separated plant shadows, other shadows, textured material children,
   Arctic, depth and material colors. Distinguish export inclusion from initial
   PSD visibility, and channel/group ordering from the viewport display mode.
   Verify PhotoCraft import preserves these groups, alpha, blend modes and hidden
   layers before recording. Do not substitute a flat composite or an invented
   editor if that verification fails. Use a review copy; the inspection step
   must not accidentally return a new AI reference edit or overwrite the PSD.
6. Switch context explicitly to the Web Studio. Establish its real workspace
   once, then enlarge or split only as needed. Show PSD import/handoff, one
   whole-image result, layer AI participation, a child draft, description and
   Update, then the genuine sliding comparison. Show one canvas edit with
   Apply parent, arrow/text/reference inside its context boundary and the
   corresponding result. Preserve parent/source traceability; do not narrate
   a white draft as generated content. Finish with actual 4K refinement,
   output dimensions, image export and saved board for resuming work.

Before recording, prepare white, single-material/plant demonstration and
completed checkpoints plus the exported PSD and Web board. They should have
matching case/view identities and working assets. Record actual generation
outcomes; label shortened waits or previously completed results. Keep UI state
changes, narration and the right-side image consistent. Verify important
results before writing claims into the spoken script. Advanced archiving,
backup limits and exhaustive parameter explanations can stay outside this
introductory tutorial.

## Precise cursor coordinates

For each cue record capture dimensions, desktop DPI, capture rectangle and target
control bounds. Convert CSS coordinates to captured pixels when necessary.
Do not infer a click location from an approximate screenshot text label.

For source crop `(cx,cy,cw,ch)` contained in output `(ox,oy,ow,oh)`, use
`s=min(ow/cw,oh/ch)`, `px=(ow-s*cw)/2`, `py=(oh-s*ch)/2`. Source hotspot `(x,y)`
maps to `(ox+px+s*(x-cx), oy+py+s*(y-cy))`. Apply the same animated transform to
the image, hotspot, target and click ring. Cursor artwork needs its own hotspot
offset: its top-left pixel is not the click position. Derive the correct
transform instead if using a different fitting mode.

Inspect frames before, at and after important clicks, plus the actual resulting
UI state. Include nonzero crop origins and DPI scaling in alignment checks.
Avoid two cursors: hide the captured system cursor when adding an overlay, or
keep the captured cursor and do not add another. The large arrow must not cover
the control label. If an MCP action has no corresponding UI action, do not
invent a clickable control to explain it.

## Teaching rhythm

Show context, approach, pause, click, then allow the new state to register.
Explain consequences rather than narrating every movement. Keep material and
plant comparisons aligned. Short D wipes suit chapter boundaries in this brief;
do not interrupt continuous actions with unnecessary transitions. No zoom pulses
or meaningless drift. Respect native Rhino cameras for real model navigation.

Capture the English interface at enough resolution for legible final close-ups.
Check at intended playback size; 4K source alone does not guarantee readability.
Keep subtitles clear of controls; highlight one target at a time. Use
`Generation time shortened` when cutting waits, and retain meaningful actual
progress/error/review states. Never simulate an instantaneous successful call.

PSD-editor illustrations may use a simplified layout, but must show actual
exported pixel layers with material children expanded. A composite does not
demonstrate editable material layers. Do not imply the illustrated editor is a
separately validated Adobe Photoshop installation.

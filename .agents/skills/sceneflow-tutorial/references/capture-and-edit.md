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
- Begin a teaching section with the full workspace. Outline the operation
  panel and model viewport with two restrained frames, then smoothly carry
  those same regions into a split layout. This establishes where the enlarged
  content comes from. Do not repeat the full introduction for every click.
- Keep settings on the left and the model on the right. Split views serve
  readability; their widths may change with the teaching focus. Enlarge the
  relevant control once, hold through the explanation/action, and return to
  context at a natural boundary. Avoid repeated enlarge/shrink pulses.
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

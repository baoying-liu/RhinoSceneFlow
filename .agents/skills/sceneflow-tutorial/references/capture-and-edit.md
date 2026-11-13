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

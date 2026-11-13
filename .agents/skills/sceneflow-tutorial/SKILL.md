---
name: sceneflow-tutorial
description: Plan, capture, narrate and edit SceneFlow tutorials using real Rhino and Web workflows, precise cursor overlays and bilingual review scripts. Use for tutorial production and revisions, not general plugin development or ordinary promotional edits.
---

# SceneFlow Tutorial

Build an understandable, reproducible user workflow. Distinguish a plan,
illustrated setup, verified operation and finished video.

## Scope and references

- For planning, use [the bilingual 15-minute cue template](assets/tutorial-15min-cues.csv).
  These are chapter timings and example sentences, not a complete spoken script.
  Adapt duration to the current request; fifteen minutes is this case's brief.
- For recording, precise cursor overlays and zoom, read
  [capture and edit](references/capture-and-edit.md).
- For voice, subtitles and delivery, read
  [narration and verification](references/narration-and-verification.md).
- Find the current RhinoSceneFlow repository and read its `AGENTS.md` before
  automation. Follow its sandbox/original MCP boundaries. This skill supplies no
  permission to install into production Rhino or modify unrelated work.

## Connect the production assets

Give each demonstrated action a stable cue ID shared by its English script,
Chinese translation, capture/UI state, target rectangle, cursor/click events,
narration file and subtitle cues. A revised sentence invalidates its dependent
audio/subtitles, not unrelated footage.

Use current English labels and the actual public download. Keep these meanings
distinct: AI sign-in versus MCP connection; PSD visibility versus AI
participation; object versus layer application; draft creation versus AI
generation; editable parameters versus immutable result pixels.

## Present the product accurately

- Capture genuine Rhino/Web states for the main tutorial. Cropped footage stays
  real; reconstructed UI must not invent controls or success states.
- When requested, match installer illustrations to the real installer and label
  them `Illustrative setup`. Do not show personal credentials or account screens.
- Keep one teaching case progressing from white model to finished result. Show
  actual separate material layers in the PSD section.
- Use a large, precisely aligned cursor. Transform image, cursor hotspot and
  target with the same crop/zoom transform. Inspect actual click frames.
- Establish context before a close-up; hold steady while explaining or clicking.
  Avoid zoom pulses, arbitrary shaking and decorative cursor movements.
- Follow the current test Rhino's actual theme, docked layout and enabled tool
  icons. Establish the full workspace, outline the settings panel and model
  viewport, then smoothly reframe those same regions into readable split views.
  See the confirmed case direction in [capture and edit](references/capture-and-edit.md).
- Explicitly label compressed waits. Queued or unverified work is not completed.

## Tools and acceptance

Use available Remotion skills for implementation, captions and rendering;
Playwright for real Web operations; original Rhino MCP for permitted model/UI
operations. Read the relevant installed skill when first using that workflow.
An MCP state change is not authentic UI click footage: record the corresponding
real UI action, or identify the visual as an illustration.

Keep private voice files, credentials and signed URLs outside Git. New paid
generation, publication and account mutations need task authorization; a skill
supplies none. Do not consume allowances merely to exhaust them.

Verify the entire export, sampled interactions, readable UI, subtitle/audio
timing and delivered files. Report pronunciation, likeness and product issues.
ASR cannot prove voice similarity; a rendered still cannot prove interaction.
Correct transcription also cannot prove fluent speech: missing consonants,
swallowed syllables, stuttering and damaged sentence joins fail narration QA.
The v02 sample's framing was accepted; its voice fluency still needs repair.
Follow the short-segment and listening checks in the narration reference before
scaling to a full tutorial.

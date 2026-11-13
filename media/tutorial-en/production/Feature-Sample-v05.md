# Feature sample v05

120 seconds, 1920×1080, 30 fps, English visual presentation and original instrumental score. This is an effect-and-pacing sample for the user to review before further production or AI generation. It does not replace the longer tutorial.

## Visual rules

- Fixed camera and image scale for material, plant parameter and season changes. Matched hard cuts intentionally preserve comparison; there is no zoom pulse, light flash, whip or camera shake in those changes.
- Floating condensed controls explain the actual feature sequence rather than displaying a full application window. They are designed workflow visualizations, not screen recordings or a promise that generation is instant. Material and plant output assets are real previously generated SceneFlow resources; the single-object material before/after and hand-added plant come from the actual plugin operations previously captured in an owned B copy.
- Camera motion: new native Rhino frames for a six-second white opening and a ten-second human→overhead→axon route (including a hold), captured separately for every output frame without sparse-frame blending. The camera projection remains parallel; this sample does not claim a perspective-to-parallel morph. Two sun captures use the same final camera with 18°/52° altitude and 135° azimuth. Named views and source model are preserved through the existing CaptureScope; no source scene is saved over.
- PSD uses the earlier exploded-plane design and a recognizable layer list. Entry shrinks the source view once; the layer group zooms in once, holds a fixed focus window for successive channels, and withdraws once. Background planes fade behind the active channel to avoid transparent stacking obscuring it. This is a concept layer workspace with actual PSD channel images.
- D angled reveal has fixed image size. Result stability is shown using cropped recordings of the actual Web divider, not a synthetic split effect. The crop isolates the native image area and actual handle.
- Local-edit gesture is visualized against its actual submitted image; its final result is real. The 4K section uses a separately saved actual output as a delivery example, not a claim that it was generated from the immediately preceding local edit. Final production should regenerate a consistent selected camera/style lineage after approval.
- 4K has one continuous zoom-in and hold; no reset or rebound. The final logo is static apart from a short fade.

## Music

Original synthesized score from make-sample-score-v05.py, arranged to the scene boundaries: anticipation, sparse interaction, pulse, organic planting, build, airy camera flight, restrained export, a quieter layer section, AI intent, result reveal, comparison breathing room, local refinement, final lift and resolution. Section RMS spans roughly -26.7 to -14.8 dBFS before the video volume setting; the arrangement changes instrumentation/density as well as loudness. Includes brief arranged breaks before key entries. No external music, purchased samples, voice cloning or paid service was used. No new image generation was performed in this sample task.

## Coverage

See chapters.json / the watch page for the exact 14 section positions. The existing case supports the visual demonstration; broader species/material variants, final camera continuity at section boundaries and a fully consistent edited-image→4K source chain are production follow-ups, not completed claims.

## Validation

ESLint/TypeScript passed. Twenty-one representative frames rendered and visually reviewed; active PSD channel legibility was improved after review. Final duration, frame rate, video/audio decoding, chapter navigation and browser seeking are checked after export. Image detail in a 1080p movie is not a replacement for the actual source 4K PNG.

Final export checks: duration exactly 120 seconds; H.264 1920×1080 at 30 fps, AAC stereo 48 kHz. Full FFmpeg decode passed. Browser seeking at ten section points passed with readyState 4 and no media errors. Fourteen chapter buttons are exposed on the local watch page. The latest PSD focus frame was visually checked from the encoded MP4.

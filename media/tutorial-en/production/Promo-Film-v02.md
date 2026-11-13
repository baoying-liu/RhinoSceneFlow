# SceneFlow Intro v02

A 120-second, 1920×1080, 30 fps introduction with English titles and an original 120 BPM instrumental score. This is the cinematic introduction, not the longer narrated tutorial.

## Timeline

- 00:00 White model / opening
- 00:06 AI material request and physical UV application
- 00:18 Plant generation and mixed planting
- 00:30 Camera orbit, crown plan and human view
- 00:40 Random seeds, size range and individual plant edit
- 00:48 Seasonal orbit
- 01:00 Sun, named view resolution and PSD export
- 01:08 Six actual PSD channels in a conceptual layer workspace
- 01:22 Short brief, expanded intent, auxiliary channels and multiple actual AI styles
- 01:32 Spatial annotation and actual local facade edit
- 01:42 Actual 4096×2304 refinement result
- 01:52 White model to final image / end card

## Source and accuracy

Native Rhino B camera captures: 120 azimuth frames each for white, cedar, summer, autumn and winter, plus 120 elevation-transition frames. Adjacent native frames are blended for the camera sequence. These are actual perspective captures, not rotation of a flat still image.

All scene, plant, material, PSD channel and final AI imagery comes from the Hillside SceneFlow example. The model and library remain intact. UI panels and cursor gestures are designed interaction visualizations, not continuous screen recordings. The layer workspace is conceptual, not Adobe Photoshop. Generation/refinement duration is compressed; no speed promise is made. The original 4K output is presented inside a 1080p video.

Music: production/make-film-score.py creates the 120-second stereo score using deterministic synthesis; no third-party recordings, purchased music, voice cloning or external paid music service. Export score metrics are in out/promo-film-v02/score.json.

## Rebuild

Use the pinned package-lock.json (Remotion 4.0.543). Run npm ci, generate the music with the project's Python environment, and run npm run lint. Restore the case imagery into public/case/promo-20261112 and public/case/promo-film-v02. These media assets and render outputs are excluded from Git and delivered with the shared video source assets.

Composition: SceneFlow-Promo-Film-v02. Render using npx remotion render SceneFlow-Promo-Film-v02 out/promo-film-v02/SceneFlow-Intro-v02.mp4 --codec=h264 --crf=18 --concurrency=4. Let Remotion use its bundled browser. This CLI version rejects the literal free-license key; eligible personal free use renders without a license-key argument. No paid license was purchased or activated.

## Checks

ESLint and TypeScript passed. Twelve representative frames were rendered and visually reviewed before final export. Final media duration, resolution, frame rate, codec, audio and browser seeking are checked after rendering.

Final validation: full FFmpeg decode passed; H.264 1920×1080 at 30 fps, stereo AAC 48 kHz, duration exactly 120 seconds. Browser seek/play passed at 2, 24, 50, 74, 90, 109 and 118 seconds with readyState 4 and no media errors. The preview server supports byte ranges.

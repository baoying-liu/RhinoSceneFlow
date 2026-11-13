# Feature sample v05.1 — material scale and plan plants

This is a media/case correction, not a new plugin release. Sandbox B remains on 0.23.3. No new AI image calls, source geometry edits, forced global plan mode or source model overwrite.

## Material correction

The v05 rapid material sequence reused earlier captures whose brick/terracotta appearance was inconsistent with fresh native application. Re-captured all four variants through `material_apply` on an owned copy, with the same Named View, model and summer planting. Do not diagnose a UV renderer defect solely from a previously exported still. Fresh native custom-mapping versus native one-meter box comparison did not reproduce that appearance discrepancy; the original mappings were restored.

The brick asset had a 1×1 m coverage. For this demo it is now 1.6×1.6 m: eight horizontal modules and twenty courses give nominal 200×80 mm modules including joints. This is an explicit demo scale choice, not measured manufacturer data. Metadata revision advanced from 1 to 2; original PNG bytes remain unchanged. Cedar retains 1.2×2.4 m, terracotta 1.6×1.6 m. The four-repeat random bake keeps coverage at 4.8×9.6 m for cedar and 6.4×6.4 m for terracotta; do not apply unbaked repeat factors to a baked bitmap.

Native effective base-color repeat receipts: brick .625/.625; terracotta .15625/.15625; limestone 1/1; cedar .2083333333/.1041666667. Exact receipts and captures are under ignored `artifacts/material-plan-audit-v05` and `public/case/promo-sample-v05/fixes`.

## Plant correction

All sixteen map files for the two species were present, independently SHA-256 checked and decoded, including their seasonal plan images. This was not missing-image fallback. The old close perspective overhead pose pointed down but its camera-to-plant rays did not reach the configured 75° plan threshold; forcing plan was diagnostic only and was reverted.

B's runtime lift was .65; set it to the requested .2. Preserve automatic mode and the 75° threshold. The corrected native camera route increases camera distance smoothly up to 4× while narrowing its frustum proportionally, and widens the overhead framing to keep the site visible. It returns to the original final pose. Each of 300 output frames is captured by native Rhino with explicit Rendered attributes, without image-frame interpolation.

Measured frames 150/179/195/210: all 15 plants use plan images; every raised-anchor offset divided by the scaled tree height equals .2. Frames 0/299: all 15 return to elevations. This tests this route and these two assets, not every possible camera or asset. Picking/export implementations were not changed.

## Preservation and checks

Owned capture model only; original `SceneFlow-Home-Ready.3dm` reopened with 70 objects and Modified=false. Native plugin binaries and UV algorithm unchanged. ESLint and TypeScript pass. The original v05 movie is retained; corrected output is in `out/promo-sample-v05.1`.

Final output checks: 120 s, H.264 1920×1080 30 fps with AAC 48 kHz; full FFmpeg decode passed. Browser seeks at 9/19.7/54.5/92/112 s all reached readyState 4 with no media error. Copied the output to the local OneDrive project folder and verified matching SHA-256; cloud sync is not verified.


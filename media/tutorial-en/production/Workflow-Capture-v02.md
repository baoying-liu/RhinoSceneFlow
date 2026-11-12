# Workflow capture study v02

2026-11-12. SceneFlow 0.23.2, RhinoDevSandbox B. English promotional assets.

## Review

Open http://127.0.0.1:3149/out/workflow-keyframes-v02/review.html while the local preview server is running. The gallery also exists at `../out/workflow-keyframes-v02/review.html`.

Seven 3840 x 2160 keyframes cover material chat/application, planting controls, camera modes, seasons, PSD channels, three AI styles and an annotated local edit. The chat, controls and layer dock are presentation concepts using actual output images; they are not recordings of the shipping interface. Remotion source: `../src/PromoWorkflowKeyframes.tsx`.

## Actual software outputs

- 68 native Rhino captures at 1920 x 1080: white model, four material alternatives, mixed/species planting, random layout/scale/mirror changes, individual editing, sun changes and four seasons.
- Eight real orbit camera poses, plus human, top and axon views. These are key poses, not a continuous flight recording. Top-plan and human-elevation switching was checked against the actual plant-instance state.
- Two plant records: Betula nigra / River birch and Acer rubrum / Red maple, each with four seasons and elevation/plan PNGs. Together with four grass variants and a new terracotta texture, the collected set contains 21 PNG files. Some summer images were reused; this does not mean 21 new generation calls.
- Three layered PSDs: Human, Top and Axon, 1280 x 720. Plants, separate shadows, textures, Arctic, depth and material-color channels were decoded independently with psd-tools. Depth and color channels are hidden in the PSD. Channel previews were mapped by actual layer names, not assumed stack order.
- Three completed Web Studio styles: Monet-inspired impressionism, Starry Night-inspired night painting and a hand-painted animated-film background.
- A completed annotated local edit changes the small front timber facade to teal. Pixel comparison found 14,079 changed pixels inside the 14,080-pixel editable mask and zero changed pixels outside it.
- Completed 4096 x 2304 Monet refinement: six tiles, all completed; final full PNG exported and dimensions checked. This is the final composite, not a partial preview or a simple enlargement.

Raw images: `../public/case/promo-20261112/`. The review manifest includes keyframe checksums. Full task records, prompts, masks, package receipts and original PSDs are under repository `artifacts/promo-production-20261112/`.

## Saved case and assets

The original Hillside model and earlier avoidance-test document were preserved. The final owned case is `artifacts/promo-production-20261112/SceneFlow-Promo-Final.3dm`; `final-save.json` is the save receipt. A prior checkpoint is retained separately. Images remain external library assets rather than embedded bitmaps.

Eleven material ZIPs were exported through SceneFlow's native material-package operation to `asset-packages/`, with map hashes checked against each package's asset.json. Plant PNGs and metadata are retained in `assets/`. This is not yet a separately tested one-click portable demo installer; reopening on another computer needs library import/path resolution.

Owned Web board: `53f7ded7262a44d8ac1215eb2f86db44` (SceneFlow Promo - Hillside - 2026-11-12). Inputs, ancestry, descriptions, parameters and annotations remain in that board. Its save-package receipt is in `web/board-package.json`. Global language/climate/generation preferences were restored; the demo model was returned to summer, cedar and its mixed baseline planting.

## Findings and next production pass

- Direct model saves inside an active Platform command stalled. User Esc recovered the command; deferred idle saves with all input suppressed succeeded. Keep save orchestration out of the active command for recording automation.
- PSD seasonal suffixes still exported in Chinese despite English UI. Original files were retained; byte-identical English-named copies were made for production. This product issue was not silently treated as fixed.
- Seasonal plants need artistic review before the final edit, especially the dense brown winter birch crown plan. Botanical identity metadata does not guarantee biological accuracy of generated imagery.
- AI stylization can alter edges and fine geometry. Passing tile checks is not a guarantee of pixel-identical architectural form.
- The next video pass needs densely sampled real camera flight, timed interaction animation and music editing. The previous 20-second sample was preserved; this collection does not pretend to be a new finished film.

All application operations used the original Rhino MCP Platform and SceneFlow APIs on B. No user mouse control or production-Rhino deployment was used.

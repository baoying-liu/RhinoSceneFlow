# SceneFlow 0.23.1 — first public preview

Rhino → AI materials / physical UV → planting → layered PSD → Web AI postproduction.

## Download and install

Download **SceneFlow-Setup-0.23.1-win-x64.exe** below. GitHub's automatically generated
source ZIP is not the installer. Compare its SHA-256 with **SHA256SUMS.txt**.

Requires Windows x64, a licensed copy of **Rhino 8.34 or later in the Rhino 8
series**, and Rhino's **.NET 8 runtime mode**. Save your work and close standard
Rhino before running the EXE. Installation targets standard Rhino for the current
Windows user, not sandbox B. Remove any previous ZIP/Yak/manual SceneFlow plugin
registration first; retain your libraries and projects.

Run **`RhinoSceneFlow`** after installation. The environment/sign-in check runs on
startup. If verification fails, use **Go to settings** in the chat area.
Your own Codex CLI installation, ChatGPT sign-in, Internet and image access/quota
are required for AI. The installer does not include an AI subscription. The local
Web workbench uses the same Codex authorization.

[Installation guide](https://github.com/baoying-liu/RhinoSceneFlow/blob/master/docs/Getting-Started.md)

## Included

- AI material and transparent plant assets, existing-asset search and local shared libraries.
- Physical-scale UV, xatlas-based complex mesh unwrapping, material application and variation.
- Parametric planting groups, Plants List, seasons and camera-facing display.
- Batch Named View PSD export: materials, plants, shadows, Arctic mode and depth.
- Web list/canvas views, annotations, image ancestry, PhotoCraft editing reference layers,
  whole-image exploration and HD processing.
- Dockable native tools, English/Chinese UI and original McNeel MCP automation.
- EXE packaging with private runtimes, startup verification and repair/uninstall UI.

## Preview limitations

- **Unsigned.** Windows cannot verify the publisher. Automatic installation
  of updates is disabled; later previews require manual installation. Do not disable
  security protections for unexpected or mismatched downloads.
- **Not stable.** Clean-machine install, repair, uninstall,
  cross-version upgrade/rollback and a fresh recipient account login have not
  completed acceptance. These are known validation gaps, not passing tests.
- Existing sandbox B feature checks, native/core regressions, actual private-runtime
  workflow tests and read-only MSI/extraction checks have passed. No production Rhino
  installation was performed as part of these checks.
- Legacy Yak/manual installs are detected and blocked with removal instructions;
  automatic migration is not implemented. Back up libraries, boards and models.
- No promise of model-perfect AI geometry, globally seamless UV or unrestricted
  material/renderer compatibility. Start with a copied scene and low-resolution output.
- Application uninstall is designed to retain user materials, plants, boards,
  authorization and shared MCP/WebView2; the full maintenance lifecycle remains unverified.

## Dependencies

Bundled original McNeel Rhino MCP Platform 0.3.0, private CPython and image libraries,
.NET worker runtimes and Microsoft's original WebView2 bootstrapper. WebView2 needs
Internet if absent. Source/build material for libvips and its dependencies is supplied
in **SceneFlow-ThirdParty-Sources-0.23.1.zip**; normal users need only the EXE.

[Third-party notices and project licensing status](https://github.com/baoying-liu/RhinoSceneFlow/blob/master/THIRD-PARTY-NOTICES.md).
No open-source license for SceneFlow's own original code is selected in this preview;
the explicit third-party licenses remain in effect.

Please report reproducible problems in [Issues](https://github.com/baoying-liu/RhinoSceneFlow/issues).
Include versions and sanitized screenshots, never authentication files, bearer URLs
or confidential project assets.

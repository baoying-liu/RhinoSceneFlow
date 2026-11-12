# Install the public preview

## Requirements

- Windows x64, licensed Rhino **8.34 or later in the Rhino 8 series**, .NET 8 host.
- Save your work and close standard Rhino before install, repair, upgrade or uninstall.
- AI features require Internet, a separately installed supported Codex CLI, your own
  ChatGPT sign-in and account access/quota for image generation. SceneFlow does not
  include an AI subscription or promise image access for every account.
- No global Python installation is required. Private Python and image dependencies
  are included. Original McNeel Rhino MCP Platform 0.3.0 is bundled; compatible
  installed versions are reused. If WebView2 is missing, its bootstrapper needs Internet.

## Install

1. Download `SceneFlow-Setup-0.23.1-win-x64.exe` and `SHA256SUMS.txt` from
   [Releases](https://github.com/baoying-liu/RhinoSceneFlow/releases).
   Verify the downloaded file with PowerShell `Get-FileHash -Algorithm SHA256`.
   This preview is unsigned; its publisher is not yet verified by Windows.
2. If a previous ZIP/manual/Yak SceneFlow copy is installed, remove that old
   SceneFlow registration/package first. Keep your materials, plants and boards.
   The installer detects conflicting ownership and stops rather than overwriting it.
3. Run the EXE for your current Windows user. It targets standard Rhino 8, not a
   RhinoDevSandbox channel. Do not install by copying individual DLLs from the source.
4. Start Rhino and run **`RhinoSceneFlow`** to open the dockable workspace.
   If Rhino is using another .NET runtime, consult Rhino's `_SetDotNetRuntime`
   command and select .NET 8, then restart; the installer does not change it silently.
5. The initial environment/sign-in check runs automatically. If verification fails,
   choose **Go to settings**, then **Connections and updates**.
   Install Codex from the official guide linked there if missing, use browser/device
   sign-in, then run **Check environment and sign-in** again.
   A successful check confirms local prerequisites and sign-in, not image quota.

The Web workbench shares the same local Codex authorization; no separate sign-in
is required. Image access, quota and network availability still depend on your
account and service provider.

## First workflow

1. **AI assets:** select a Rhino object, describe a material or plant and optionally
   add reference images. Existing suitable library assets are searched first.
2. **Materials / UV:** apply to the selected object or its layer. SceneFlow checks
   physical-scale UV before application. Test a copy of your model first.
3. **Plants:** select library plants, build a composition and place/scatter onto
   supported surfaces. Plants List manages groups and isolated editing.
4. **PSD:** run `RhinoSceneFlowPanel`, create/select Named Views, set resolution,
   seasons and layer channels, then export. Begin at 1K before large output.
5. **Web:** run `RhinoSceneFlowPostProduction`, send/select a PSD, create a child
   draft, add a brief and update it. Review a whole-image result before HD refinement.
   List and canvas share the same images, versions and ancestry.

## Repair, uninstall and data

Run the same EXE again for Repair or Uninstall, or use Windows Installed apps.
Save and close standard Rhino and active SceneFlow jobs first. Application files
live under `%LOCALAPPDATA%/Programs/RhinoSceneFlow`. Libraries, boards and account
authorization are not installer-owned files and are retained. Shared McNeel MCP
and WebView2 are retained too. Back up your models and user library before testing.

The public preview has not completed clean-machine install/repair/uninstall/upgrade
acceptance. Its current validation includes sandbox B functionality, read-only MSI
table inspection, payload extraction and private-runtime regressions. These do not
constitute a real installation lifecycle test. Automatic installation of updates
is disabled in this unsigned preview; install subsequent previews manually.

## Feedback

Use [Issues](https://github.com/baoying-liu/RhinoSceneFlow/issues). Include SceneFlow
version, Rhino version, UI language, the command/tool, reproduction steps and a
sanitized screenshot. Do not attach private models, authentication or bearer URLs.

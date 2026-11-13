# SceneFlow 0.23.3 — public preview

Whole-image AI renders now use the original image's aspect ratio directly.
Previously, a landscape image was placed inside a square white canvas; if the
image model moved that padding, cropping back at fixed coordinates could leave
a white band in the final render.

- New whole-image inputs and edit masks match the target canvas.
- Output with an incompatible aspect ratio is rejected before publication,
  rather than stretched or cropped by guessing white margins.
- Saved older tasks retain their original input-coordinate handling.
- Protected pixels and source transparency remain exact during local edits.

Validated in RhinoDevSandbox B with landscape/portrait/square edge-pixel tests,
PSD participation and protection tests, canvas/workflow tests, and an actual
1280 × 720 local repair. The real repair removed the top white band while keeping
every pixel outside the editable strip unchanged. This does not guarantee that
an image model will never invent a frame or change architectural details.

## Install or update

1. Download **SceneFlow-Setup-0.23.3-win-x64.exe** from this release. GitHub's
   source-code ZIP is not an installer.
2. Save your work and close standard Rhino before running the EXE.
3. Follow the installer, then start Rhino 8 and run **RhinoSceneFlow**.
4. Review [Getting Started](Getting-Started.md) for prerequisites and AI sign-in.

The EXE targets standard Rhino for the current Windows user, independently of
the development B channel. It includes the private image-processing runtime,
original McNeel MCP Platform package and required notices. User libraries and
boards are retained during repair/uninstall.

This remains an **unsigned preview**, not a signed stable release. Windows may
warn about an unknown publisher. Automatic installation of updates remains
disabled pending trusted signing. Clean-machine install/repair/uninstall and
upgrade acceptance are still outstanding; installer extraction checks do not
replace those tests. AI calls consume the user's account allowance or applicable
credits; a supported ChatGPT login is required.

Known limitation: importing an older board package can retain its imagery while
showing some result nodes as pending. Keep the original exported images and
inspect the input/result state before regenerating.

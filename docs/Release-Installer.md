# SceneFlow 0.23.1 public preview

The first public distribution is tagged `v0.23.1-preview.1` and marked Pre-release.
It is unsigned and is not a clean-machine installation/upgrade acceptance certificate.
No production installation is performed by development builds or the read-only
installer test. See [Getting-Started.md](Getting-Started.md) for recipient instructions.

## User workflow

The existing Settings tool has one collapsible **Connections and updates** section.
It provides environment/account checking, supported Codex browser and device-code
login, original McNeel MCP documentation, public stable-release checking, verified
download and an explicit save/exit/install action. Environment detection does not
consume image quota. Account login is distinct from image-model access and quota.
It does not inspect ChatGPT desktop credentials or edit MCP client configuration.

Compared with a separate first-run modal wizard, the reusable Settings section
retains context, works after installation, and keeps repair/update discoverable.
Installation itself uses WiX Burn's standard maintenance UI and MSI transaction,
rather than maintaining our own installation database and custom deletion logic.

## Formal Rhino versus B

The EXE targets the current user's standard **Rhino 8.34+ x64**. Its MSI writes only
the standard HKCU Rhino 8 SceneFlow GUID registration, pointing to
`%LOCALAPPDATA%/Programs/RhinoSceneFlow/RhinoSceneFlow.Plugin.rhp`. It does not write
RhinoDevSandbox channel catalogs, virtual registry branches, deployment snapshots,
or test Schemes. Sandbox already isolates that registry and blocks standard plugin
scan roots. Both copies use the same plugin GUID but in different registry views.
The formal installer uses Name/FileName on the GUID key itself, per
[McNeel registration documentation](https://developer.rhino3d.com/guides/rhinocommon/registering-plugins-windows/),
and requests startup loading for managed installations. Do not copy the sandbox
loader's internal registration format into a production installer.

Managed installs resolve Python from their own `Runtime/Scripts/python.exe` and
Studio data from `%LOCALAPPDATA%/RhinoSceneFlow/production/postproduction`.
Development/B retain the existing runtime and Studio directory, so current test
boards are not moved. Update state/receipts are likewise separated. Sandbox
production downloads/installation are rejected at the service boundary, not just
disabled in the UI. The native installer probe permits positively identified
registry-isolated B processes, while unknown/standard Rhino instances block it.

Libraries are user data, not installer payloads. They can still be intentionally
shared using existing library settings and file locks. This is not a promise of
data isolation when users deliberately select the same library folder.

## Installer ownership

`scripts/Build.ps1` builds and validates the application. Then:

```powershell
./scripts/Build-Installer.ps1
./scripts/Test-Installer.ps1 -Version 0.23.1
```

Output: `artifacts/installer/0.23.1/SceneFlow-Setup-0.23.1-win-x64.exe`.
MSI/Burn own install, same-version repair, uninstall and major upgrades. Downgrades
are rejected. Installer requires standard Rhino and owned production Python/texture
workers to be closed; it never terminates them. User libraries, plants, boards,
account authorization and shared MCP/WebView2 are not owned by the application MSI
and are retained on uninstall.

Prerequisites bundle original McNeel Rhino MCP Platform **0.3.0** Yak (SHA-256 pinned,
MIT notice retained), and Microsoft's signed Evergreen WebView2 bootstrapper.
Compatible installed MCP versions are reused. WebView2 is installed only when
absent and needs Internet in that case. Python, image libraries, libvips and the
texture/updater .NET runtimes are privately staged into the application. No global
Python, PATH, SDK or credentials are installed or copied.

The previous offline cache contained ChatKit only and could not support the current
PSD pipeline. Release CPython 3.14.10 uses a separate, explicitly pinned compatible
wheel set in `installer/requirements.txt` (psd-tools 1.12.1, Pillow 12.2.0,
numpy 2.3.5, OpenCV 4.13.0.92), unlike the development Python 3.11 environment.
Frozen installed versions and wheel hashes are bundled. Real raster regression
tests must run with the staged interpreter. Build scripts refuse bad archive hashes,
missing imports and unsigned/untrusted external runtime installers. Bytecode/debug
files are excluded from MSI file ownership.

**Legacy limitation:** a Yak/manual SceneFlow installation is detected and blocked
with removal instructions, rather than silently creating a second owner. Users must
remove only the old SceneFlow package/registration before the first MSI install;
libraries remain intact. Fully automatic legacy migration is not implemented.

## Updates

The plugin queries the unauthenticated GitHub latest-stable Release API for
`baoying-liu/RhinoSceneFlow`. A private repository/no release has a distinct status.
Only exact `SceneFlow-Setup-{version}-win-x64.exe` assets with a GitHub SHA-256 digest
qualify. Download size/hash are checked, then Windows Authenticode trust and a pinned
publisher certificate are verified. Redirected download content still must pass both.
No executable is launched on a missing certificate, signature failure or sandbox host.

Build with `-PublisherThumbprint <code-signing certificate thumbprint>` to configure
the publisher and sign the final EXE. The current preview is unsigned and therefore
**does not enable automatic installation**. No signing key is generated, bundled
or read from another application. Automatic update installation in a stable release
needs a real signing identity. An explicitly unsigned public preview is distributed
for manual installation only.

The explicit update action rejects active native tasks and asks the owned Studio
service to stop gracefully (it rejects active image tasks). Updater binaries are
copied to a private runner snapshot so MSI can replace installed binaries. The helper
validates the parent PID/start time, waits without killing it, verifies the installer
again and launches Burn. Cancelling Rhino exit cancels that pending helper. Other
standard Rhino instances still block installation. Successful plugin initialization
shows a one-time per-user/version acknowledgment; installer exit alone is not proof
the plugin loaded. Old runners/downloads are currently retained, not auto-cleaned.

MSI rollback covers its installation transaction. This is not a whole-user-data
rollback or a tested automatic recovery from a new plugin that loads incorrectly.

## Remaining release gates

- Clean Windows installation, real repair/uninstall and version-to-version upgrade,
  cancellation and transactional rollback on a disposable VM; current read-only
  MSI-table/layout checks do not replace this.
- Publisher certificate, signed update exercise with real Release assets, and
  GitHub repository/history/license preparation before publication.
- Test the browser and device-code authorization flow on a recipient account;
  current account-status checks do not prove new-user authorization or image access.
- Confirm standard Rhino uses its supported .NET 8 host. Do not silently modify
  another user's Rhino runtime setting; document `_SetDotNetRuntime` if required.
- Automatic legacy Yak migration and post-load failure rollback are future work.

# Code signing policy

Status: proposed SignPath Foundation application, not submitted or approved.
No currently published SceneFlow artifact is claimed to be foundation-signed.

## Responsibility

Repository owner `baoying-liu` maintains the project and is the proposed signing
approver. External contributions must be reviewed before release. Signing will
require manual approval of the exact source commit and build artifact. The owner
must enable multi-factor authentication on GitHub and the signing service before
an application is submitted; this document is not evidence that it is enabled.

Only project-owned binaries may be signed using a project signing subscription.
Upstream components keep their own signatures/licenses and must not be re-signed
as SceneFlow. Required product/version metadata must match the approved release.
No repository secret, account token or private key belongs in distributed files.

## Application readiness

- Original SceneFlow code now uses MIT, explicitly chosen by the owner.
- Source-to-binary build provenance must be verified by the provider. The manual
  candidate workflow now uses pinned official SDK references instead of requiring
  an installed Rhino. Its first hosted run passed on commit `9e10efe`:
  [candidate build](https://github.com/baoying-liu/RhinoSceneFlow/actions/runs/43256136730).
  Later product/version metadata changes passed locally; the eventual signed
  release must build its exact approved commit again. Provider acceptance of the
  provenance remains required. An arbitrary local EXE is not a substitute.
- Rhino is proprietary host software and is not bundled. WebView2's Microsoft
  redistributable/SDK libraries are proprietary dependencies that must be disclosed
  for eligibility review; do not assume the system-library exception applies.
- The owner must accept provider terms and approve the application. Any contact
  details or provider account forms must be supplied through the provider directly.
- A signed release and its own project identity must be verified before enabling
  automatic installation. Do not replace the publisher pin with a broad trust of
  every package signed by a shared foundation certificate.

If approved, update this policy and the download page with the provider's required
attribution and final team roles. Do not advertise that attribution as an existing
sponsorship before approval.

See [SignPath Foundation conditions](https://signpath.org/terms),
[privacy](Privacy.md), and [release readiness](Release-Readiness-0232.md).

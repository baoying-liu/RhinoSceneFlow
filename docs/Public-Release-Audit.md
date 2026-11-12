# First public preview: publication review

Prepared 2026-11-12 for `v0.23.1-preview.1`, application version 0.23.1.
This is a scoped engineering review, not a security certification or legal opinion.

## Source and privacy

- Reviewed the 26 pre-release commits and the staged release changes using
  Gitleaks 8.30.1, with redacted reports retained outside Git. The scanner download
  was checked against its GitHub asset SHA-256.
- One historical generic-key alert was manually identified as the public SHA-256
  of PhotoCraft's attribution file. `.gitleaksignore` excludes only that exact
  historical fingerprint; no broad directory/rule suppression was added.
- History and staged scans then returned no findings. This is not proof that every
  possible sensitive string is detectable.
- History filename inventory found no `.env`, auth.json, credentials, certificate
  private keys, user 3dm/PSD files or conversation JSONL paths. The only historical
  blob above 1 MB is the upstream PhotoCraft binary part, with provenance/licenses.
- No GitHub Actions runs or webhooks existed at review. No history was rewritten.
- Build artifacts, runtimes, raw local receipts, personal libraries and login files
  remain outside the source commit. Release metadata excludes authenticated URLs.

## Distribution

- Recipient guide, explicit preview limits, security/privacy guidance and top-level
  third-party notices added. No new license grant was selected for original code.
- Installer now includes .NET and libvips notices/source instructions. Original
  McNeel, Python package, browser and PhotoCraft licenses are retained.
- A separate source supplement contains 37 upstream archives/patches plus version,
  URL/hash and MXE-snapshot metadata. Every included archive was opened for validation.
  This does not claim that the upstream binaries were rebuilt by SceneFlow.
- Application build and core/native caption validations passed. Packaged ChatKit
  and Studio source bytes match the release tree (the version marker is compared
  without BOM/newline differences).
- Private release Python passed BoardWorkflow, TaskInputs and real HTTP late-Codex
  discovery regressions with zero image/model calls.
- Read-only installer checks passed: 6,912 MSI file rows, standard registration,
  upgrade rules, repair mode, required notices, native probe, Burn extraction and
  bundled-MSI identity. Production registration stayed unchanged.
- Actual Windows Authenticode tests accepted the original Microsoft prerequisite
  and rejected a wrong publisher, unsigned SceneFlow EXE and missing publisher pin.

## Unverified / release classification

No clean disposable Windows/Rhino environment was available. Real first install,
maintenance, version-to-version upgrade/rollback and fresh recipient login remain
unverified. No production installer was executed to replace that missing test.
Sandbox B feature evidence is documented separately in Validation.md / Sandbox-B.md.

Therefore this release is **Pre-release / unsigned / manual installation**, with
automatic installation of updates disabled. It is not a stable-release acceptance.

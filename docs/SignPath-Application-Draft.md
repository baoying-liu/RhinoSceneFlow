# SignPath Foundation application draft

Not submitted. This document does not claim provider approval or sponsorship.
Use the owner's own contact details in the provider form, never repository secrets.

## Project

- Name: SceneFlow for Rhino 8
- Repository: https://github.com/baoying-liu/RhinoSceneFlow
- Download page: https://github.com/baoying-liu/RhinoSceneFlow/releases
- Original-code license: MIT, explicitly selected by the owner on 2026-11-12
- Maintainer / proposed signing approver: repository owner `baoying-liu`
- Policy: https://github.com/baoying-liu/RhinoSceneFlow/blob/master/docs/Code-Signing-Policy.md
- Privacy: https://github.com/baoying-liu/RhinoSceneFlow/blob/master/docs/Privacy.md

## Description

SceneFlow is an independently maintained Windows plugin for Rhino 8. It supports
AI-assisted material and transparent plant asset creation, physical-scale UVs,
editable planting groups, layered PSD view export, and an authenticated local Web
workspace for traceable AI image postproduction. AI access uses the user's own
supported account and model access. It does not bundle account credentials.

## Build and signing request

The project has a manually dispatched GitHub Actions candidate build. It builds
project source using hash-pinned official Rhino SDK references, runs portable
tests, stages a private Python runtime, builds EXE/MSI packages, and inspects their
contents without installing them. The initial hosted build passed on `9e10efe`:
https://github.com/baoying-liu/RhinoSceneFlow/actions/runs/43256136730 . Later signing
metadata additions passed locally; build the exact approved release commit again
for signing. Provider acceptance of provenance is still required. There is no
current signing step or stable-release publication step.

We would like to sign project-owned plugin/worker/installer binaries and preserve
all upstream licenses/signatures. Binary metadata restrictions and nested-package
signing order still need to be configured with SignPath. We will not re-sign
third-party binaries using a project certificate.

## Dependencies to disclose

Rhino itself is proprietary prerequisite host software and is not distributed in
the package. The installer includes original McNeel Rhino MCP Platform (MIT),
WebView2 SDK libraries and Microsoft's original WebView2 runtime bootstrapper,
CPython and its packages, .NET runtime, libvips and PhotoCraft. Exact notices are
in THIRD-PARTY-NOTICES.md; runtime locks and provenance accompany the build.

Please confirm eligibility of the proprietary WebView2 redistributables/SDK under
your dependency rules before we claim that the package qualifies. We also request
guidance on safely identifying this project's signed updates if the signing
certificate is shared between foundation-supported projects. Current updater
trust checks remain disabled for unsigned packages.

## Owner checks before submission

- Confirm GitHub two-factor authentication and enable required SignPath MFA.
- Supply the preferred personal name/contact email directly in the provider form.
- Review provider terms, requested permissions and the actual application fields.
- Verify hosted build evidence, product/version metadata and privacy opt-outs.
- Approve the final application text. No application has been sent automatically.

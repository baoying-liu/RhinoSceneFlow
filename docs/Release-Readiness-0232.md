# 0.23.2 stable-release readiness

Status: preparation only. Do not describe this build as signed or as having passed
installation acceptance. The owner authorized proceeding toward a stable release,
then explicitly deferred paid signing while alternatives are investigated.

## Signing decision

No usable personal code-signing certificate/private key was found in this build
machine's CurrentUser or LocalMachine certificate stores. No paid resource or
third-party signing application has been created.

- Azure Artifact Signing supports US individual developers. It requires the
  owner's Azure subscription and personal identity validation. Basic is currently
  USD 9.99/month, not free. The owner elected not to purchase it at this time.
  [Setup](https://learn.microsoft.com/en-us/azure/artifact-signing/quickstart),
  [pricing](https://learn.microsoft.com/en-us/azure/artifact-signing/how-to-change-sku).
- SignPath Foundation offers free signing for qualifying open-source projects,
  using the Foundation as certificate publisher. The owner accepted evaluating
  this route and explicitly selected MIT for original code, now in LICENSE.
  Eligibility, dependency exceptions, verified build provenance, MFA and provider
  approval remain unresolved. The application has not been submitted.
  [Conditions](https://signpath.org/terms).
- OSSign currently reports applications suspended due to its backlog.
  [Provider status](https://ossign.org/).
- A self-signed certificate is not a replacement for public Windows trust.

If Azure is selected later, its rotating signing certificates must not be pinned
by leaf thumbprint. The current updater intentionally still requires a fixed
trusted certificate: implement and test durable certificate-profile identity
validation before enabling that signing provider. Do not remove publisher checks.
[Microsoft certificate management](https://learn.microsoft.com/en-us/azure/artifact-signing/concept-certificate-management).

## Engineering preparation

Office packaging exposed missing home-only cached inputs and a dependency on the
global `py` launcher. Runtime staging now fetches exact hash-pinned CPython and pip
inputs when absent, checks Authenticode on embedded Python, and downloads target
wheels using that embedded interpreter. Only building the pure-Python pyvips
wrapper uses the explicit development interpreter (default: SceneFlow's development
venv); it does not require `py.exe`. No global Python is installed or changed.
Failed build logs remain under ignored artifacts. This does not make transitive
wheel resolution immutable: the runtime's generated lock/provenance must be
reviewed with each release.

The initial unsigned 0.23.2 package passed read-only installer checks: 6,912 file
rows, production registration unchanged, native probe exit 0 and exact bundled
MSI extraction. Its staged Python passed BoardWorkflow, TaskInputs,
Test-PostProductionRaster and Test-ReviewTaskSync with synthetic inputs and no
model calls. Windows trust/publisher rejection tests also passed. Adding the
newly authorized MIT license and privacy document changes the package and requires
a new package/hash check; none of these checks is an actual install/upgrade test.

## Remaining acceptance gates

1. Choose a signing provider, complete its validation, and verify final signed
   package identity and integrity. Rebuild after configuring publisher identity.
2. Test first install, repair, uninstall and version-to-version upgrade in a
   disposable Windows/Rhino environment. The owner currently has none; B tests
   and read-only installer extraction do not substitute for this.
3. Exercise the real AI failure/retry path and the signed update lifecycle,
   preserving source files and task provenance.
4. Review English release documentation, dependency notices, secrets and exact
   final package bytes; then publish a stable GitHub Release. Until these gates
   pass, leave the existing public pre-release unchanged.

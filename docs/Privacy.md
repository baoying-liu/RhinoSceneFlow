# Privacy policy

SceneFlow stores material/plant libraries, models, PSD exports, boards, task records
and diagnostics locally in the configured folders. These files may contain private
project information. Do not attach them to public issues without reviewing them.

## Network use

- AI generation, prompt assistance and botanical research use the configured AI
  and research services. Selected images, descriptions, references and other task
  inputs may be sent to those services when the corresponding action is requested.
  Account login and image access use the user's own supported Codex sign-in flow.
- Opening asset chat loads the ChatKit browser component from OpenAI's CDN.
  Authentication can contact the provider's login servers. See
  [OpenAI privacy information](https://openai.com/policies/privacy-policy/).
- Standard managed installations check GitHub Releases for updates on startup by
  default. Disable **Check for updates on startup** under Settings > Connections
  and updates to stop automatic checks. Downloads occur through explicit update
  actions. See [GitHub privacy information](https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement).
- The installer may install missing Microsoft WebView2, requiring a Microsoft
  download. Existing shared WebView2 and Rhino MCP installations are retained on
  uninstall. Browser/runtime behavior is governed by their vendors; see
  [Microsoft privacy information](https://privacy.microsoft.com/privacystatement).
- Local Web interfaces use authenticated loopback connections. Do not expose their
  ports or bearer URLs publicly. No promise is made that third-party providers do
  not retain submitted content; review their current policies before confidential
  work.

Uninstall preserves user libraries, boards and account authorization. Delete those
separately only after backing up the data you want to keep; revoke provider access
through its supported account controls. Do not send credentials to the maintainer.

This policy must be revisited if telemetry, crash uploads or other external data
flows are added. Signing-provider build metadata is separate from users' models
and is not permission to upload user project files.

# Security and privacy

Do not post API keys, Codex authentication files, bearer URLs, personal models,
PSD files, or unredacted diagnostics in public issues. Report a suspected
credential exposure using GitHub's private vulnerability reporting when available;
otherwise contact the repository owner privately before posting details.

SceneFlow's browser interfaces bind to loopback and use authenticated local
transport. Do not expose their ports to the Internet or forward authenticated URLs.
AI requests send the selected inputs and reference content to the configured AI
provider. Review those inputs before processing confidential work.

SceneFlow does not obtain authorization by reading ChatGPT desktop credentials.
It uses the user's own Codex CLI installation and supported sign-in flow. Never
send your authentication files to the project maintainer.

The first public preview is unsigned and cannot install automatic updates. Download
only from this repository's Releases and check SHA256SUMS.txt. Do not disable
Windows security protections to run an unexpected or mismatched file.

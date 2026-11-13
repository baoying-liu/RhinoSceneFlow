# Cloud reference-voice trial — 2026-11-13

User preference: attempt Next, then Plus, then Flash, then local inference.
This is a preference order, not a measured universal quality ranking. Do not
exhaust free quotas just to switch models. Account billing/quota consumption
cannot be inferred solely from a successful API response.

Next supports direct audio references in `input.references[].audio_data` and
uses `@voice1` in `input.text_prompt`; it does not require creation of a Voice ID.
The 20-second user recording was submitted with authorization, using the
Windows-encrypted credential from the private per-user vault.

The real request succeeded. Result: 144-second 48 kHz stereo PCM16 WAV,
27,648,044 bytes; usage input 4,580 tokens, output 28,800 tokens. The returned
signed audio URL used HTTP on Alibaba's Singapore OSS result host. Downloaded
the exact result through HTTPS on the same host without a second generation.
Signed URLs and raw responses remain private; do not print or commit them.

Local small.en ASR found the expected introductory sentences, followed by
repetitions, including a repeated introduction. Consequently this full output
is unsuitable as finished tutorial narration. A 23.8-second opening excerpt
was delivered strictly for voice review, alongside a full-content MP3 and the
previous local 1.7B short sample. The excerpt is a time cut only; pitch, speed
and gain were not changed. Brand-name pronunciation and speaker likeness still
need user review. No full tutorial was generated.

Both Plus and Flash personal-voice creation attempts with `voice-enrollment`,
`create_voice`, and the respective target model returned HTTP 403
AccessDenied.Unpurchased. That does not negate the earlier successful Plus
system-voice synthesis. No system voice was represented as a personal clone.

The cloud runner reuses an existing result rather than silently repeating a
billable request. The Plus/Flash runner accepts explicit target model selection
and separate private receipts. Audio response parsing supports inline Base64
as well as downloadable results.

Browser metadata checks passed for original, Next excerpt and local sample.
Delivery is copied to local OneDrive `SceneFlow/Voice Tests/Qwen-Model-Comparison-20261113`;
cloud synchronization is not verified.

API references:
- https://docs.modelstudio.console.alibabacloud.com/en/model-studio/audio-generation-api
- https://docs.modelstudio.console.alibabacloud.com/zh/model-studio/voice-cloning-user-guide

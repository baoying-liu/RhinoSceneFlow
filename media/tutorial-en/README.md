# SceneFlow English walkthrough

Personal open-source project presentation for company sharing. Target: 23 minutes,
maximum 30. English narration, English application UI, English captions.

## Current state

`SceneFlow-Style-Preview` is a **72-second silent visual study**, not a completed
tutorial or new live-generation demonstration. It uses actual previously saved
case exports and PSD channel thumbnails. The screen recordings and cloned
narration have not been produced. The planned timing includes deliberate holds
for real operations and is not an audio-aligned final timeline.

Run `npm ci`, prepare the local assets, then `npm run dev -- --port=3147`.
`prepare-assets.py` reads the repository's ignored existing case exports and
requires psd-tools and Pillow (the SceneFlow development runtime has them).
It preserves the source PSD and writes local provenance with file hashes.

The editable preview uses deterministic frame-based animation and authored scene
boundaries. No generated imitation of the application UI is used as a tutorial
screen recording. `production/storyboard.json` is the complete editorial draft,
including narration, shot lists, prompts, timing and capture rules.

## Voice and network

The office network reached the international Model Studio console and login
fields. An unauthenticated POST to the international speech customization endpoint
returned 401 InvalidApiKey, proving basic network reachability only. Mainland
speech API requests were reset on both GET and POST. No account authentication,
voice upload or speech generation has been verified, and the cause of the reset
has not been established. Diagnostic receipts remain under artifacts/video-production.

Raw voice references must stay outside the Studio public directory and outside
Git. Use `production/voice-reference.txt` for the short English recording. Confirm
the provider account, model access, network completion and cost before cloning.
Do not put API keys, login files, personal browser state or reference recordings
in this project. Actual UI capture must use owned B/browser windows and redact
account details and local personal paths.

## Remaining work

- Review the visual study and script hierarchy.
- Complete one authenticated, short English speech test and review pronunciation.
- Record the actual current English B tools and Web workflow, including one
  honest failure/retry example. No new whole/4K AI generation has been requested
  or paid for by this media setup.
- Align final speech, operation holds and caption JSON; derive final SRT.
- Check every chapter, privacy redactions, source/result labels, sync and final
  exported dimensions before delivering MP4 and the editable project.

SceneFlow's source license does not relicense Remotion. Use of this production
tooling follows Remotion's own current license. No paid services have been enabled.

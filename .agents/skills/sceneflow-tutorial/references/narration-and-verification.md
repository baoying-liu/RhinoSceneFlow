# Narration, subtitles and verification

## Voice production

Share cue IDs across English narration, Chinese review translation, action and
audio. Outline sentences are examples, not a complete timed script. Budget the
actual narration and interaction pauses; do not stretch a promo to fifteen
minutes or accelerate UI until it is unreadable.

Current preference: cloud Next, then Plus, then Flash, then local Qwen. This is
the user's preference, not a universal quality ranking. Verify capabilities,
prices and actual quota evidence. A system-voice success does not prove custom
voice creation is enabled. Do not exhaust quotas just to change models.

Next supports direct audio references; Plus/Flash may require a Voice ID bound
to their exact target model. Verify current official contracts and avoid mixing
legacy `qwen-voice-enrollment` with new `voice-enrollment` fields. Existing
implementations/evidence are in `media/tutorial-en/production/`:
`qwen_next_trial.py`, `qwen_voice_trial.py`, `qwen_local_trial.py`,
`Cloud-Qwen-Voice-Trial.md` and `Local-Qwen-Voice-Trial.md`.

Use the private Windows credential vault without exposing its decrypted key.
Use only authorised voice samples. Preserve private receipts before retrying a
potentially billable call. Inspect/download the existing response before another
generation: an empty audio data field does not imply failed synthesis. Handle
inline audio and signed result URLs without logging them. Never substitute a
system voice and claim it is the user's clone.

Generate short semantic units with a consistent reference and delivery. Review
SceneFlow/Rhino/UV/PSD/MCP pronunciation, missing or repeated words, unexpected
sounds, clipping and silence. ASR flags content errors; it cannot establish
speaker likeness. Have the user review the voice sample before full narration.
A nine-second success does not validate long-form reliability.

The current full Next trial repeated text. Its labelled clean excerpt is only
a voice review asset, not a solution to production repetition. Repair/reject
bad segments and recheck them. Do not conceal failures under music or equate
receipt duration with usable tutorial narration.

## Subtitles and edit handoff

Tie English subtitles to the final spoken track. Deliver SRT and burned-in
captions. Chinese belongs in the review table unless otherwise requested.
Re-time captions after voice/shot edits. Follow the installed captions skill;
prefer at most two readable lines, phrase breaks and enough reading time.
Keep controls visible beneath captions and callouts.

Music should remain below intelligible narration and be sparse while teaching.
Retain unprocessed voice masters. Check cuts for clicks and clipped consonants.
Keep frame rate, chapter timing and source provenance in the edit manifest.

## Final verification

- Decode the whole export; confirm dimensions, frame rate, audio and duration.
  Review speech audibility with the music enabled.
- Inspect click hotspots, focus transitions, typed text, actual UI outcomes and
  subtitle timing/wrapping at key action points.
- Demonstrate actual separate PSD materials, correct comparison orientation,
  final image dimensions and saved board ancestry.
- Verify playback/seeking and local review links. Hash-check copies; distinguish
  local OneDrive delivery from confirmed cloud sync. Retain editable sources and
  the prior accepted cut.
- Report plan/sample/full-video scope and unresolved issues. Do not claim fresh
  installation testing, long-form voice consistency or geometric invariance
  from unrelated or synthetic evidence.

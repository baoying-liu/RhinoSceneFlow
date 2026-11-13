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

## Speech fluency gate before full production

The user found stuttering and swallowed sounds in the v02 tutorial sample.
The voice identity and visual direction were usable, but the speech track is
not a final narration master. Do not reuse it unchanged throughout the full
tutorial. The cause is not yet isolated: synthesis, pause removal, joins or
encoding may contribute; compare stages rather than claiming a diagnosis.

- Finish the spoken English script against current UI labels first. Use short,
  natural sentences and consistent pronunciation for Rhino, SceneFlow, UV, PSD,
  MCP and 4K. Preserve UI spelling in subtitles even when spoken text expands
  an acronym. Avoid introducing long, comma-heavy text just to fit a chapter.
- Generate short semantic passages, usually one to three sentences, with the
  same voice reference and delivery. Prefer a complete thought over a rigid
  character or duration limit. Do not generate the whole fifteen minutes as
  one request. Keep enough neighboring context for a consistent delivery.
- Retain the untouched response and a separate edited track for each cue.
  Audit for repetitions, omissions and abnormal silence before assembly.
  ASR/word timestamps help find faults; they are not a listening substitute.
- Compare the original synthesis, processed cue, cue-to-cue join and encoded
  video audio. Check sentence starts/ends and quiet consonants especially.
  If listening is unavailable, mark auditory QA unverified rather than pass.
- Trim at complete phrase boundaries in silence, retaining short handles
  around speech (roughly 80–150 ms is a useful starting point, adjusted by
  listening). Word timestamps may be inaccurate; never cut exactly at every
  recognized word or remove all breathing pauses. Add tiny fades only in
  silence; do not crossfade overlapping spoken words.
- If a syllable is swallowed, a word is slurred, speech stutters or prosody is
  unnatural, regenerate the affected complete sentence/passage and compare it.
  Do not repair it by cutting within a word, aggressive time compression,
  speed changes or denoising, and do not mask it with music. Preserve accepted
  neighboring passages. Bound retries; after two unsuccessful replacements,
  investigate reference/settings or an authorized fallback instead of looping.
- Keep speech speed comfortable. Build the visual edit around the usable
  narration and genuine interaction pauses; shorten the script if needed to
  fit the tutorial budget. Do not force the voice to match old frame counts.
- Make a representative corrected passage first, including technical terms
  and a sentence join. Record content, pronunciation, fluency and edit-boundary
  review separately from voice likeness. Existing approval of the speaker
  identity does not approve a new defective passage, nor require a new account
  or voice enrollment for routine retries.

Only passages without known speech defects belong in the final master.
Retain failed cue IDs/issues so a later edit cannot silently reintroduce a bad
take. Match both subtitles and bilingual review timings to the replacement
audio, not to the original defective take.

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

# Local Qwen voice trial — 2026-11-13

Tutorial scope is now approximately 15 minutes, English UI/narration, focusing on
materials, planting, layered PSD export and Web AI refinement. This file records
a voice feasibility trial, not a completed tutorial.

## Isolated setup

- Runtime: `%LOCALAPPDATA%/RhinoSceneFlow/qwen-tts-runtime`, Python 3.12.16.
- CUDA PyTorch 2.11.0+cu128, matching torchaudio, qwen-tts 0.1.1,
  transformers 4.57.3, accelerate 1.12.0. `uv pip check` passed.
- Model: official `Qwen/Qwen3-TTS-12Hz-1.7B-Base`, including its bundled speech
  tokenizer, under `%LOCALAPPDATA%/RhinoSceneFlow/qwen-models/`.
- GPU: RTX 5070 Ti Laptop, 12 GB. No Rhino runtime changes or cloud API calls.
- Original/reference audio, local ASR transcripts and generated voices stay in
  the private per-user production directory, outside Git. Never commit them.
- `qwen_local_trial.py` sets Hugging Face / Transformers offline flags before
  imports. Model downloads happened separately; synthesis used local files.

## Results and limitations

The first longer deterministic/greedy trial produced low-level unintelligible
audio and reached its generation limit. It was rejected, not delivered as a
successful clone. A shorter trial using the model's default sampling succeeded.
These two changes do not isolate the exact cause of the first failure.

Successful sample: 8.96 seconds, 24 kHz mono PCM16; synthesis 28.26 seconds,
total model/prompt/generation 38.01 seconds, peak allocated GPU memory 4.64 GiB,
peak reserved 5.10 GiB. Peak audio level -3.4 dBFS, mean -23.4 dBFS. No gain,
pitch, music or other post-processing was applied to the delivered WAV.

Local small.en ASR recovered the intended sentence but recognized SceneFlow as
SyncFlow. This flags pronunciation review; it is not a voice-similarity metric.
Speaker likeness/naturalness requires the user's listening review. A nine-second
sample does not validate the consistency of a full 15-minute narration. Segment
generation and speech-content checks remain necessary for production.

The optional SoX executable was not installed; its import-time warning did not
prevent this generation. FlashAttention was not installed; the model used SDPA.

The listening page includes the unchanged original recording and successful
sample. Both browser audio elements loaded metadata without media errors.
Delivery: local OneDrive `SceneFlow/Voice Tests/Local-Qwen-1.7B-20261113`;
cloud synchronization is not verified.

Sources: https://github.com/QwenLM/Qwen3-TTS and
https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-Base .

# AI Dubbing Studio

![AI Dubbing Studio](https://img.shields.io/badge/status-production-blue) ![Python](https://img.shields.io/badge/python-3.10%2B-blue) ![Flask](https://img.shields.io/badge/framework-flask-orange)

Turn any video or audio file into a version people in another country can actually watch and understand — same content, different language, same feel.

AI Dubbing Studio takes a source recording, transcribes what's being said, translates it, generates a new voice track in the original speaker's voice, and (if the source was a video) drops that new audio back onto the original footage. What comes out the other end is a dubbed, downloadable file, ready to publish.

---

## Table of Contents

1. [Why this exists](#why-this-exists)
2. [What it actually does](#what-it-actually-does)
3. [How it's built](#how-its-built)
4. [The workflow, step by step](#the-workflow-step-by-step)
5. [Using the API](#using-the-api)
6. [Where the logic lives](#where-the-logic-lives)
7. [What's next](#whats-next)
8. [License](#license)

---

## Why this exists

Localizing video content is usually slow, expensive, and split across five different tools — a transcription service, a translator, a voice actor or TTS tool, and someone stitching it all back together in a video editor. Most small teams and independent creators just skip it and lose their audience outside their home language.

AI Dubbing Studio puts the whole chain in one place. Upload a file, pick a target language, and get back a translated voice track — in the speaker's own cloned voice — and a fully dubbed video if that's what you uploaded. No editing software, no manual syncing, no juggling five different accounts.

It's built to be genuinely usable, not a demo. Every stage of the pipeline — transcription, translation, and voice cloning — is handled by purpose-built models chosen specifically for speed and output quality, not just whatever was easiest to wire up.

---

## What it actually does

- **Takes audio or video** — MP3, WAV, OGG, FLAC, M4A, MP4, MOV, AVI, MKV, WEBM. Whatever format your file is in, it's probably supported.
- **Transcribes speech with word-level accuracy** using WhisperX, which gives tighter timestamps than plain Whisper — the kind of precision dubbing actually needs to stay in sync.
- **Translates sentence by sentence** through the Groq API, not as one giant block of text. This keeps timing sensible, keeps translation fast, and makes the output easier to read or edit later.
- **Clones the original speaker's voice** using Zonos-2 and generates the translated line in that same voice, so the dub still sounds like the person who said it — not a generic narrator.
- **Cleans up the audio** before translation if you want — normalizes loudness, removes some of the harshness, gets it to a consistent level.
- **Rebuilds the video** with the new audio track dropped in, keeping the original picture untouched.
- **Gives you everything to download** — the dubbed audio, the translated transcript, and the final video, all from one dashboard.

Nothing here needs a video editing background. If you can drag a file into a browser window, you can use this.

---

## How it's built

At a high level, this is a normal web app: a browser front end talking to a Flask backend, which in turn hands work off to a processing pipeline.

The browser sends the uploaded file to the Flask server. The server checks the file, pulls the audio out if it's a video, and passes it to the pipeline. The pipeline handles transcription, translation, and voice generation, then hands a finished result back to the server, which serves it to the browser for playback and download.

**The core stack:**

- **WhisperX** for transcription — word-level timestamp alignment on top of Whisper, which matters a lot once you're trying to keep dubbed speech synced to picture.
- **Groq** for translation — fast, segment-by-segment translation so pacing stays close to the original instead of getting flattened into one paragraph.
- **Zonos-2** for voice cloning — takes a short reference of the original speaker and generates the translated line back in their own voice, rather than a generic TTS voice.
- **FFmpeg** for everything audio/video — extraction, cleanup, and reassembly.
- **Flask** for the backend, serving a lightweight browser front end.

Keeping these stages separated means a change to any one model or provider doesn't risk breaking the upload flow or the video handling. Each part does one job.

---

## The workflow, step by step

**1. You upload a file and set your options.** Pick a source language, a target language, whether you want audio enhancement, and whether voice cloning is on.

**2. If it's a video, the audio gets pulled out.** FFmpeg extracts a clean mono audio track so the rest of the pipeline has something consistent to work with, regardless of what video format came in.

**3. Optional cleanup pass.** If enhancement is turned on, the audio gets normalized and resampled before anything else happens to it. This tends to noticeably improve transcription accuracy on noisy recordings.

**4. Transcription.** WhisperX breaks the audio into timestamped segments with word-level alignment — not one wall of text, but individual lines with a precise start and end time each, close to how subtitles are structured.

**5. Translation, segment by segment.** Each line gets sent to Groq and translated on its own rather than as one big paragraph. This keeps the pacing closer to the original and avoids the translator collapsing meaning across sentence boundaries.

**6. Voice cloning and generation.** A reference of the original speaker's voice is passed to Zonos-2 along with the translated line, producing a new voice track that sounds like the same speaker, now saying it in the target language.

**7. Reassembly, if it was a video.** The new audio gets placed back onto the original video stream. The picture is never touched — only the sound changes.

**8. Delivery.** Links to the finished audio, transcript, and (if applicable) video show up in the dashboard, ready to download.

---

## Using the API

The core of the app is a single endpoint.

**`POST /api/dub`** — accepts a multipart form with the source file and your settings (`audioFile`, `srcLang`, `tgtLang`, `outputFormat`, `enhanceAudio`, `voiceClone`, `voiceMethod`), and returns a JSON object with links to the generated audio, transcript, and video.

A trimmed example of what comes back:

```
{
  "audioUrl": "/outputs/abc123_dubbed.wav",
  "translatedText": "Hello and welcome to the dubbing studio.",
  "isVideo": true,
  "videoUrl": "/outputs/abc123_dubbed.mp4"
}
```

The full response also includes a `translatedSegments` array with per-line timing and text, which is what the transcript viewer in the UI reads from. That same array is exactly what you'd need if you ever want to export subtitles later — the timing data is already there.

**`GET /outputs/<filename>`** serves any generated file directly, which is how the download links in the dashboard actually work.

---

## Where the logic lives

Transcription runs through WhisperX, which layers forced alignment on top of Whisper's raw output — the result is segments with word-level timestamps instead of just rough sentence boundaries, which is what makes the eventual dub feel synced rather than approximate.

Translation happens one segment at a time through Groq rather than on the whole transcript at once. It's a small design choice, but it matters — translating line by line keeps the pacing of the original speech intact.

Voice generation runs through Zonos-2, which takes a reference clip of the source speaker and produces the translated line in a cloned version of that voice. This is the piece that makes the output feel like a dub of the person rather than a voiceover replacing them.

Everything that touches FFmpeg — pulling audio from video, cleaning up sound, or reattaching a new audio track — is wrapped in small functions that check FFmpeg is installed before doing anything, and fail with a clear error if it isn't.

---

## What's next

Things on the roadmap, roughly in order of priority:

- Subtitle export (SRT/VTT) straight from the existing segment data
- Speaker detection, so multi-voice recordings get matched more accurately
- Batch uploads for handling several files in one go
- Automatic source language detection
- A background job queue, so large files don't tie up the request while processing
- User accounts and saved project history

None of these require rearchitecting anything — the pipeline was built with this kind of extension in mind from the start.

---

## License

See the LICENSE file in this repository for terms.

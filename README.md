# AI Dubbing Studio

![AI Dubbing Studio](https://img.shields.io/badge/status-production-blue) 
![Python](https://img.shields.io/badge/python-3.10%2B-blue) 
![Flask](https://img.shields.io/badge/framework-flask-orange)

Turn any video or audio file into a version people in another country can actually watch and understand — same content, different language, same feel.

AI Dubbing Studio takes a source recording, transcribes what's being said, translates it, generates a new voice track, and (if the source was a video) drops that new audio back onto the original footage. What comes out the other end is a dubbed, downloadable file, ready to publish.

---

## Table of Contents

1. [Why this exists](#why-this-exists)
2. [What it actually does](#what-it-actually-does)
3. [How it's built](#how-its-built)
4. [The workflow, step by step](#the-workflow-step-by-step)
5. [Getting it running](#getting-it-running)
6. [Configuration](#configuration)
7. [Using the API](#using-the-api)
8. [Project layout](#project-layout)
9. [Where the logic lives](#where-the-logic-lives)
10. [Extending it](#extending-it)
11. [Troubleshooting](#troubleshooting)
12. [What's next](#whats-next)
13. [License](#license)

---

## Why this exists

Localizing video content is usually slow, expensive, and split across five different tools — a transcription service, a translator, a voice actor or TTS tool, and someone stitching it all back together in a video editor. Most small teams and independent creators just skip it and lose their audience outside their home language.

AI Dubbing Studio puts the whole chain in one place. Upload a file, pick a target language, and get back a translated voice track — and a fully dubbed video if that's what you uploaded. No editing software, no manual syncing, no juggling five different accounts.

It's built to be genuinely usable, not a demo. The pipeline runs locally where it can (speech recognition happens on your own machine), and only reaches out to external services where it makes sense, like premium text-to-speech voices.

---

## What it actually does

- **Takes audio or video** — MP3, WAV, OGG, FLAC, M4A, MP4, MOV, AVI, MKV, WEBM. Whatever format your file is in, it's probably supported.
- **Transcribes speech locally** using a local Whisper-based model, so your content doesn't have to leave your machine just to get a transcript.
- **Translates sentence by sentence**, not as one giant block of text. This keeps timing sensible and makes the output easier to read or edit later.
- **Generates a new voice track**, with a choice of text-to-speech engines depending on the quality and cost you're after.
- **Cleans up the audio** before translation if you want — normalizes loudness, removes some of the harshness, gets it to a consistent level.
- **Rebuilds the video** with the new audio track dropped in, keeping the original picture untouched.
- **Gives you everything to download** — the dubbed audio, the translated transcript, and the final video, all from one dashboard.

Nothing here needs a video editing background. If you can drag a file into a browser window, you can use this.

---

## How it's built

At a high level, this is a normal web app: a browser front end talking to a Flask backend, which in turn hands work off to a processing pipeline.

The browser sends the uploaded file to the Flask server. The server checks the file, pulls the audio out if it's a video, and passes it to the pipeline. The pipeline handles transcription, translation, and voice generation, then hands a finished result back to the server, which serves it to the browser for playback and download.

Nothing about this needs to be exotic — it's a fairly standard request/response flow with some heavier processing happening in the middle.

**The main pieces:**

- `web/` — everything the user sees and interacts with: the upload screen, progress bar, transcript viewer, and download links.
- `app.py` — the server. Handles uploads, talks to FFmpeg for audio/video work, and calls into the pipeline.
- `pipeline.py` — the actual dubbing logic: transcribe, translate, generate speech, return a result.
- `module/` — small, separate adapters for transcription, translation, and text-to-speech, so any one of them can be swapped out without touching the rest of the app.
- `uploads/` — where incoming files land temporarily.
- `outputs/` — where finished, downloadable files get saved.

Keeping these separated means a change to, say, the translation provider doesn't risk breaking the upload flow or the video handling. Each part does one job.

---

## The workflow, step by step

**1. You upload a file and set your options.**
Pick a source language, a target language, whether you want audio enhancement, and which voice engine to use (or leave it on automatic).

**2. If it's a video, the audio gets pulled out.**
FFmpeg extracts a clean mono audio track so the rest of the pipeline has something consistent to work with, regardless of what video format came in.

**3. Optional cleanup pass.**
If enhancement is turned on, the audio gets normalized and resampled before anything else happens to it. This tends to noticeably improve transcription accuracy on noisy recordings.

**4. Transcription.**
The audio is broken into timestamped segments — not one wall of text, but individual lines with a start and end time each, close to how subtitles are structured.

**5. Translation, segment by segment.**
Each line gets translated on its own rather than as one big paragraph. This keeps the pacing closer to the original and avoids the translator collapsing meaning across sentence boundaries.

**6. Voice generation.**
The translated lines are joined and sent to the text-to-speech engine, producing a new voice track in WAV or MP3.

**7. Reassembly, if it was a video.**
The new audio gets placed back onto the original video stream. The picture is never touched — only the sound changes.

**8. Delivery.**
Links to the finished audio, transcript, and (if applicable) video show up in the dashboard, ready to download.

---

## Getting it running

You'll need Python 3.10 or newer, `pip`, and FFmpeg available on your system path. Git is handy for cloning the repo but not required.

Clone the project, install the dependencies, and copy the example environment file:

```powershell
cd AI-Dubbing-Tool
python -m pip install -r requirements.txt
copy .\config\.env.example .\config\.env
```

Start it up:

```powershell
python app.py
```

That's a local development run. For anything beyond your own machine, put it behind a proper WSGI server — Gunicorn on Linux, Waitress on Windows work well:

```powershell
gunicorn --bind 0.0.0.0:5000 app:app
```

A few things worth doing before you go further than a quick test:

- Use a virtual environment so dependencies don't clash with anything else on your machine.
- Never commit `config/.env` — it's meant to hold your API keys.
- Confirm FFmpeg is actually installed and reachable (`ffmpeg -version` should just work in your terminal).
- If you're deploying somewhere offline, pre-download the Whisper model ahead of time.

---

## Configuration

Everything runtime-related is set through `config/.env`.

| Setting | What it controls |
|---|---|
| `WHISPER_MODEL` | Which local transcription model to use — `small`, `medium`, or `large`. Bigger means more accurate, and slower. |
| `WHISPER_DEVICE` | `cpu` or `cuda`. GPU speeds transcription up a lot if you have one available. |
| `ELEVENLABS_API_KEY` | Needed only if you're using ElevenLabs for voice generation. |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to your service account file, needed only if you're using Google Cloud TTS. |

You don't need every key filled in — the app falls back to a free TTS option if you leave the premium engines unconfigured.

---

## Using the API

The core of the app is a single endpoint.

**`POST /api/dub`** — accepts a multipart form with the source file and your settings (`audioFile`, `srcLang`, `tgtLang`, `outputFormat`, `enhanceAudio`, `voiceClone`, `voiceMethod`), and returns a JSON object with links to the generated audio, transcript, and video.

A trimmed example of what comes back:

```json
{
  "audioUrl": "/outputs/abc123_dubbed.wav",
  "translatedText": "Hello and welcome to the dubbing studio.",
  "isVideo": true,
  "videoUrl": "/outputs/abc123_dubbed.mp4"
}
```

The full response also includes a `translatedSegments` array with per-line timing and text, which is what the transcript viewer in the UI reads from. That same array is exactly what you'd need if you ever want to export subtitles later — the timing data is already there.

**`GET /outputs/<filename>`** serves any generated file directly, which is how the download links in the browser actually work.

---

## Project layout

```text
AI-Dubbing-Tool/
├── app.py                  server, routes, file handling
├── pipeline.py              transcribe -> translate -> speak
├── config/
│   └── .env.example
├── module/
│   ├── transcribe.py        speech-to-text
│   ├── translate.py         translation
│   └── tts.py                text-to-speech
├── outputs/                 finished files
├── uploads/                  incoming files
├── web/
│   ├── index.html
│   ├── script.js
│   └── style.css
└── requirements.txt
```

The idea behind the split is simple: `app.py` deals with the outside world (HTTP, files, FFmpeg), `pipeline.py` deals with the actual dubbing logic, and everything provider-specific — which TTS engine, which translator — lives in `module/` where it can be swapped without touching anything else.

---

## Where the logic lives

The transcription step uses a local Whisper model through `faster-whisper`, so audio doesn't need to be sent anywhere external just to get a transcript. It hands back a list of segments, each with a start time, an end time, and the recognized text.

Translation happens one segment at a time rather than on the whole transcript at once. It's a small design choice, but it matters — translating line by line keeps the pacing of the original speech, and if a translation provider is ever swapped out, only `module/translate.py` needs to change.

Voice generation supports several engines — ElevenLabs and Google Cloud TTS for higher-quality output, Coqui as a self-hosted option, and gTTS as a no-key fallback that always works. The app picks the best available option automatically unless you tell it otherwise.

Everything that touches FFmpeg — pulling audio from video, cleaning up sound, or reattaching a new audio track — lives in `app.py`, wrapped in small functions that check FFmpeg is installed before doing anything, and fail with a clear error if it isn't.

---

## Extending it

**Adding a new TTS engine:** write an adapter in `module/tts.py`, wire it into the selection logic, then add the option to the dropdown in `web/index.html`. That's the whole process — nothing else in the app needs to know it exists.

**Adding a new translation provider:** same pattern. New module under `module/`, update the adapter logic in `translate.py`, add any credentials to `.env.example`.

**Adding subtitle export:** the segment data already carries start and end times for every translated line, so writing that out as an SRT or VTT file is mostly a formatting exercise, not new plumbing.

The separation between `app.py`, `pipeline.py`, and `module/` exists specifically so changes like these stay contained instead of rippling through the whole codebase.

---

## Troubleshooting

**"ffmpeg is required..." error** — FFmpeg isn't installed, or it isn't on your system path. Install it and confirm `ffmpeg -version` runs from your terminal.

**Unsupported file type** — double check the extension. Supported inputs are `.mp3`, `.wav`, `.ogg`, `.flac`, `.m4a` for audio, and `.mp4`, `.mov`, `.avi`, `.mkv`, `.webm` for video.

**Empty or missing transcript** — usually means the source audio is silent, too quiet, or the Whisper model hasn't downloaded correctly. Try a short, clear audio clip first to confirm the pipeline itself is healthy.

**Transcription is slow** — normal for long files on CPU. Switch to a smaller Whisper model, or set `WHISPER_DEVICE=cuda` if you've got a GPU available.

If something's still not working, check the Flask terminal output and the browser console first — most failures show up clearly in one or the other, and confirm files are actually landing in `uploads/` and `outputs/` as expected.

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


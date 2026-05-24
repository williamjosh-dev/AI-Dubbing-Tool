# AI Dubbing Studio

![AI Dubbing Studio](https://img.shields.io/badge/status-production-blue)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Flask](https://img.shields.io/badge/framework-flask-orange)

AI Dubbing Studio is a production-ready AI dubbing platform that transforms audio and video content into translated, market-ready voice-over assets. It combines local speech recognition, intelligent translation, multi-engine text-to-speech, and video audio replacement into a cohesive workflow with a premium UI.

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Product Vision](#product-vision)
3. [Key Features](#key-features)
4. [Architecture Overview](#architecture-overview)
5. [Technical Component Breakdown](#technical-component-breakdown)
6. [Core Workflows](#core-workflows)
7. [API Contract](#api-contract)
8. [Installation and Deployment](#installation-and-deployment)
9. [Configuration](#configuration)
10. [Frontend Experience](#frontend-experience)
11. [Backend Design](#backend-design)
12. [Pipeline Implementation](#pipeline-implementation)
13. [Developer Guides](#developer-guides)
14. [Troubleshooting](#troubleshooting)
15. [Extensibility and Roadmap](#extensibility-and-roadmap)
16. [Project Layout](#project-layout)
17. [Glossary](#glossary)
18. [License](#license)

---

## Executive Summary

AI Dubbing Studio is designed for creators, localization engineers, and media teams who want to convert spoken content from one language into another while preserving quality, timing, and usability.

The product extends beyond simple transcription and translation by adding:

- audio enhancement and normalization
- segmented translation output for better readability
- multi-engine TTS fallback and engine selection
- automatic video audio replacement
- a refined web dashboard for upload, progress, and output management

This README is intentionally exhaustive: it is both a user guide and a technical reference for engineers reviewing the architecture.

---

## Product Vision

> Enable anyone to convert audio and video into professional multilingual voice-over media with a single, guided workflow.

AI Dubbing Studio is built to support the following product goals:

- Rapid onboarding through a polished UI
- Transparent pipeline status reporting
- Clean output delivery for both audio and video assets
- Maintainable code with separated concerns and modular extension points
- Support for both local and external AI services with graceful degradation

---

## Key Features

- **Audio + Video Input**: Accepts MP3, WAV, OGG, FLAC, M4A, MP4, MOV, AVI, MKV, WEBM.
- **Multi-language support**: Configure source and target language for translation.
- **Segmented transcript**: Render translations with timestamps and natural breaks.
- **TTS engine selection**: Use automatic voice engine routing or explicit engine mode.
- **Audio enhancement**: Apply normalization and clarity improvements before translation.
- **Video dubbing**: Replace the audio track in input video files to create dubbed MP4.
- **Downloadable outputs**: Download final audio and dubbed video assets directly from the UI.
- **Developer-friendly**: Clear project structure, simple Flask API, and modular pipeline.

---

## Architecture Overview

AI Dubbing Studio is a standard web application with a client-server architecture.

```
+----------------+          +----------------------+          +--------------------------+
|                |   POST   |                      |   invoke  |                          |
|  Browser UI    | -------> |  Flask Backend       | --------> |  AudioTranslationPipeline |
|                |          |  (app.py)            |          |  (pipeline.py)           |
+----------------+          +----------------------+          +--------------------------+
                                  |  ^                               |  ^              
                                  |  |                               |  |              
                                  v  |                               v  |              
                          +-----------------------+           +-----------------------+
                          |  FFmpeg utilities     |           |  Speech services      |
                          |  (extract, enhance,   |           |  - Whisper            |
                          |   replace audio)      |           |  - Translator         |
                          +-----------------------+           |  - TTS providers      |
                                                              +-----------------------+
```

### Primary architectural separation

- `web/` — client-side presentation and interaction.
- `app.py` — external HTTP interface that validates upload, controls pipeline execution, and serves generated outputs.
- `pipeline.py` — business logic that composes transcription, translation, and speech generation.
- `module/` — isolated service adapters for transcription, translation, and speech synthesis.
- `outputs/` — published assets for download.
- `uploads/` — temporary storage for incoming source files.

---

## Technical Component Breakdown

### `app.py`

`app.py` is the application entrypoint. It exposes the user-facing HTTP routes, validates input, manages temporary file storage, performs optional FFmpeg-based media operations, and returns JSON metadata.

Responsibilities:

- Accept multipart file uploads
- Verify supported file types
- Extract audio from video inputs
- Enhance source audio when requested
- Invoke the translation pipeline
- Replace audio into video outputs for dubbing
- Expose generated assets under `/outputs/`
- Return structured status and error details

---

### `pipeline.py`

`pipeline.py` contains the high-level orchestration for the content translation workflow.

Responsibilities:

- Transcribe source audio into timestamped segments
- Translate each segment independently to preserve timing
- Synthesize the combined translated text
- Store optional transcripts and translated text files
- Return a normalized JSON result payload

---

### `module/transcribe.py`

This module is responsible for converting speech into text. It uses `faster-whisper` to run locally and returns an ordered list of segments with timestamps.

A typical segment looks like:

```json
{
  "start": 1.32,
  "end": 5.68,
  "text": "Hola, bienvenidos al estudio de doblaje"
}
```

---

### `module/translate.py`

This module translates text from a source language to a target language.

It is built to support reliable translation via the `deep-translator` library, but it is architected as a service adapter so another translation provider can be added later.

---

### `module/tts.py`

This module wraps multiple text-to-speech providers.

Supported voice generation engines:

- `ElevenLabs`
- `Coqui TTS`
- `Google Cloud TTS`
- `gTTS` fallback

The module chooses the best available engine based on configuration and request parameters.

---

### `web/` frontend

The frontend provides a studio-grade dashboard with:

- drag-and-drop file upload
- progress state reporting
- audio/video playback
- transcript viewer
- output metadata cards

The UI is intentionally clean and polished to match a product-ready experience.

---

## Core Workflows

### 1. Upload and configuration

The user uploads an audio or video source file. The UI provides controls for:

- source language
- target language
- audio output format
- audio enhancement toggle
- voice cloning toggle
- voice engine selection

The input is posted to `/api/dub`.

### 2. Pre-processing

If the input is video, the backend extracts audio with `ffmpeg`.

If the user enables audio enhancement, the backend applies a filter chain:

- loudness normalization
- resampling to 16 kHz
- mono conversion
- volume boost

### 3. Transcription

The pipeline performs speech recognition on the audio file and returns timestamped segments.

### 4. Translation

Each segment is translated individually. This preserves natural speech boundaries and improves transcript readability.

### 5. Synthesis

The translated content is concatenated and sent to the TTS engine. Output is saved as `WAV` or `MP3`.

### 6. Post-processing for video

If the original input was a video file, the generated dubbed audio is reattached to the original video while keeping the source video stream intact.

### 7. Output delivery

The API responds with URLs for:

- dubbed audio
- translated transcript
- dubbed video (when applicable)

The frontend renders playback controls and download links.

---

## API Contract

### `GET /`

Serves the `index.html` page.

### `POST /api/dub`

Accepts a `multipart/form-data` payload with fields:

- `audioFile` — uploaded file
- `srcLang` — source language code
- `tgtLang` — target language code
- `outputFormat` — `wav` or `mp3`
- `enhanceAudio` — `on` if enabled
- `voiceClone` — `on` if enabled
- `voiceMethod` — `auto`, `elevenlabs`, `coqui`, `google`

#### Example request body

```http
POST /api/dub HTTP/1.1
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary...

------WebKitFormBoundary
Content-Disposition: form-data; name="audioFile"; filename="source.mp4"
Content-Type: video/mp4

<binary content>
------WebKitFormBoundary
Content-Disposition: form-data; name="srcLang"

es
------WebKitFormBoundary
Content-Disposition: form-data; name="tgtLang"

en
------WebKitFormBoundary
Content-Disposition: form-data; name="outputFormat"

mp3
------WebKitFormBoundary
Content-Disposition: form-data; name="enhanceAudio"

on
------WebKitFormBoundary
Content-Disposition: form-data; name="voiceClone"

on
------WebKitFormBoundary--
```

#### Example response

```json
{
  "audioUrl": "/outputs/abc123_dubbed.wav",
  "translatedText": "Hello and welcome to the dubbing studio.",
  "translatedSegments": [
    {
      "start": 0.0,
      "end": 2.1,
      "text": "Hola, bienvenidos al estudio de doblaje.",
      "translated": "Hello, welcome to the dubbing studio."
    }
  ],
  "segments": [
    {
      "start": 0.0,
      "end": 2.1,
      "text": "Hola, bienvenidos al estudio de doblaje."
    }
  ],
  "isVideo": true,
  "sourceFile": "source.mp4",
  "sourceLang": "es",
  "targetLang": "en",
  "voiceClone": true,
  "voiceMethod": "auto",
  "enhanceAudio": true,
  "videoUrl": "/outputs/abc123_dubbed.mp4"
}
```

### `GET /outputs/<filename>`

Serves generated files from the `outputs/` directory.

---

## Installation and Deployment

### Prerequisites

- Python 3.10 or higher
- `pip` package manager
- FFmpeg installed and available on the system `PATH`
- `git` (recommended for cloning the repository)

### Local setup

```powershell
cd C:\Users\HP\OneDrive\Desktop\AI-Dubbing-Tool
python -m pip install -r requirements.txt
copy .\config\.env.example .\config\.env
```

### Environment configuration

Populate `config/.env` with optional and required settings.

```text
# config/.env
WHISPER_MODEL=base
WHISPER_DEVICE=cpu
ELEVENLABS_API_KEY=
GOOGLE_APPLICATION_CREDENTIALS=
```

### Run the application

```powershell
python app.py
```

### Production-ready deployment

For production, run the Flask app behind a WSGI server such as Gunicorn or Waitress.

Example Gunicorn command:

```powershell
gunicorn --bind 0.0.0.0:5000 app:app
```

If deploying to Windows with Waitress:

```powershell
waitress-serve --listen=0.0.0.0:5000 app:app
```

### Best practices

- Use a virtual environment
- Keep `config/.env` out of source control
- Validate FFmpeg availability before running
- Pre-download the Whisper model if the environment is offline

---

## Configuration

The project uses runtime configuration for model selection and external APIs.

### `WHISPER_MODEL`

The local transcription model name used by `faster-whisper`. Example values:

- `small`
- `medium`
- `large`

### `WHISPER_DEVICE`

Set the compute device for `faster-whisper`:

- `cpu`
- `cuda`

### `ELEVENLABS_API_KEY`

If using ElevenLabs for TTS, provide a valid API key.

### `GOOGLE_APPLICATION_CREDENTIALS`

When using Google Cloud TTS, set this environment variable to the path of your service account JSON.

---

## Frontend Experience

The UI is designed with a studio-style layout and includes the following interaction patterns:

- drag-and-drop upload with file preview
- responsive field validation
- enable/disable toggles for voice cloning and audio enhancement
- progress feedback layer that tracks each stage
- transcript viewer with timestamped segments
- dynamic video panel displayed only for video inputs

### UX design principles

- Keep the workflow linear and obvious
- Avoid blocking the user with technical details
- Show actionable results immediately
- Respect both audio-only and video workflows

### Example UI architecture

The frontend code is split into three responsibilities:

1. **File capture** — `web/index.html`
2. **State orchestration** — `web/script.js`
3. **Presentation** — `web/style.css`

### Frontend behavior

A simplified interaction flow from `web/script.js`:

```js
async function startDubbing() {
  form.querySelectorAll('button').forEach((button) => button.setAttribute('disabled', 'true'));
  resultsSection.hidden = true;
  progressSection.hidden = false;
  updateProgress(10, 'Uploading file to server...');

  const requestData = new FormData(form);
  const response = await fetch('/api/dub', {
    method: 'POST',
    body: requestData,
  });

  if (!response.ok) {
    throw new Error('Server failed to process the request.');
  }

  const result = await response.json();
  renderResults(result);
  updateProgress(100, 'Complete!');
}
```

### Transcript rendering logic

The UI uses per-segment translation data to avoid large single-block transcript rendering.

```js
if (result.translatedSegments && result.translatedSegments.length) {
  const lines = result.translatedSegments.map(s => {
    const start = typeof s.start === 'number' ? s.start.toFixed(2) : s.start;
    const end = typeof s.end === 'number' ? s.end.toFixed(2) : s.end;
    return `[${start} - ${end}] ${s.translated || s.text || ''}`;
  });
  translatedText.textContent = lines.join('\n');
}
```

---

## Backend Design

`app.py` is intentionally lean. Its main responsibilities are routing, validation, media conversions, and coordination with the pipeline.

### Media utility functions

#### `extract_audio_from_video`

Extracts a mono 16 kHz WAV track from the uploaded video source.

```python
def extract_audio_from_video(video_path: Path, audio_path: Path) -> Path:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg is required to extract audio from video. Install ffmpeg first.")

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ar",
        "16000",
        "-ac",
        "1",
        str(audio_path),
    ]
    run_ffmpeg(command)
    return audio_path
```

#### `enhance_audio_file`

Applies loudness normalization and resampling.

```python
def enhance_audio_file(input_path: Path, output_path: Path) -> Path:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg is required for audio enhancement. Install ffmpeg first.")

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-af",
        "loudnorm=I=-16:LRA=11:TP=-1.5,aresample=16000,volume=1.1",
        "-ac",
        "1",
        str(output_path),
    ]
    run_ffmpeg(command)
    return output_path
```

#### `replace_audio_in_video`

Reattaches the generated dubbed audio to the original video stream.

```python
def replace_audio_in_video(video_path: Path, audio_path: Path, output_video_path: Path) -> Path:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg is required to generate dubbed video. Install ffmpeg first.")

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-i",
        str(audio_path),
        "-map",
        "0:v",
        "-map",
        "1:a",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        str(output_video_path),
    ]
    run_ffmpeg(command)
    return output_video_path
```

### Request handling

The `/api/dub` endpoint performs the following sequence:

1. Verify `audioFile` is present
2. Check file type permitted by `ALLOWED_EXTENSIONS`
3. Save file into `uploads/`
4. Extract audio if the input is a video
5. Optionally enhance audio
6. Push audio into `AudioTranslationPipeline`
7. Generate audio and optionally dubbed video
8. Return JSON result to the frontend

Example route outline:

```python
@app.route('/api/dub', methods=['POST'])
def dub_audio():
    uploaded_file = request.files['audioFile']
    session_id = uuid.uuid4().hex
    saved_path = UPLOAD_DIR / f"{session_id}_{secure_filename(uploaded_file.filename)}"
    uploaded_file.save(saved_path)

    # ... validation and pre-processing ...

    pipeline = AudioTranslationPipeline(src_lang=src_lang, tgt_lang=tgt_lang, voice_method=voice_method)
    result = pipeline.run(str(audio_source), str(output_path))
    response = { ... }
    return jsonify(response)
```

---

## Pipeline Implementation

`AudioTranslationPipeline` is the heart of the business logic.

It exposes a single public method, `run`, which returns a predictable dictionary with all output metadata.

### `run` workflow

1. Validate source audio exists
2. Transcribe audio into timestamped segments
3. Translate each segment individually
4. Concatenate translated text for TTS
5. Synthesize audio into the requested format
6. Optionally write transcript files
7. Return structured metadata

### Code example from `pipeline.py`

```python
class AudioTranslationPipeline:
    def __init__(self, src_lang: str = 'es', tgt_lang: str = 'en', voice_method: str | None = None):
        self.src_lang = src_lang
        self.tgt_lang = tgt_lang
        self.voice_method = voice_method

    def transcribe(self, audio_path: str) -> List[dict]:
        return transcribe_audio(audio_path)

    def translate(self, text: str) -> str:
        return translate_text(text, src_lang=self.src_lang, tgt_lang=self.tgt_lang)

    def synthesize(self, text: str, output_path: str) -> str:
        return generate_speech(text, output_path, voice_method=self.voice_method)

    def run(self, audio_path: str, output_audio_path: str, transcript_path: str | None = None, save_translated_text: bool = False) -> dict:
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Input audio not found: {audio_path}")

        segments = self.transcribe(audio_path)
        translated_segments = []
        for segment in segments:
            seg_text = segment.get('text', '')
            translated = self.translate(seg_text) if seg_text else ''
            translated_segments.append({
                'start': segment.get('start'),
                'end': segment.get('end'),
                'text': seg_text,
                'translated': translated,
            })

        tts_text = ' '.join(s['translated'] for s in translated_segments if s.get('translated'))
        output_audio_path = self.synthesize(tts_text, output_audio_path)

        if transcript_path:
            self._save_transcript(transcript_path, segments, translated_segments)

        return {
            'input_audio': audio_path,
            'output_audio': output_audio_path,
            'translated_text': tts_text,
            'translated_segments': translated_segments,
            'segments': segments,
        }
```

### Segmented translation benefits

- Prevents huge transcript blobs
- Preserves temporal alignment for review
- Enables timestamp-aware editing or subtitles in later extensions
- Makes UI rendering predictable and performant

---

## Developer Guides

### Running pipeline directly

You can execute the pipeline from the command line with a source audio file.

```powershell
python pipeline.py uploads/source.wav outputs/translated.wav --src-lang es --tgt-lang en --transcript outputs/transcript.txt
```

### Python environment

Recommended setup:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Adding a new TTS engine

1. Extend `module/tts.py` with a new provider adapter.
2. Add selection logic in the `generate_speech` wrapper.
3. Update `web/index.html` and `web/script.js` to include the new option.
4. Add environment configuration as needed.

### Adding a new translation provider

1. Implement a new module under `module/`
2. Update `module/translate.py` adapter logic
3. Add any provider credentials to `config/.env.example`
4. Add tests for translation fallback behavior

---

## Troubleshooting

### Common issues

#### `ffmpeg` not found

If the application raises `RuntimeError: ffmpeg is required...`, install FFmpeg and ensure it is in `PATH`.

#### Unsupported file type

Only supported input sources are allowed. Confirm the filename extension is one of:

- `.mp3`, `.wav`, `.ogg`, `.flac`, `.m4a`
- `.mp4`, `.mov`, `.avi`, `.mkv`, `.webm`

#### Empty transcript or no segments

If transcription returns no segments, verify the input audio is clear and not silent. Also ensure the Whisper model is downloaded and the device is configured correctly.

#### Slow transcription

Large or high-resolution audio may take longer to process. Use a smaller Whisper model or move to GPU by setting `WHISPER_DEVICE=cuda`.

### Recommended debugging steps

1. Check logs in the browser console and Flask terminal.
2. Verify generated files appear in `uploads/` and `outputs/`.
3. Confirm `app.py` returns a JSON payload without HTML error pages.
4. Use `ffmpeg -version` to confirm FFmpeg availability.

---

## Extensibility and Roadmap

### Planned enhancements

- Add support for subtitle output (SRT / VTT) from translated segments
- Add speaker diarization and voice matching
- Add batch file upload for multi-file workflows
- Add advanced voice-editing controls and tone shaping
- Add source language auto-detection
- Add built-in asset management and favorites

### Scaling improvements

- Add a job queue for asynchronous processing
- Add persistent storage for generated assets
- Add user authentication and project dashboards
- Add cloud deployment scripts for AWS/Azure/GCP

---

## Project Layout

```text
AI-Dubbing-Tool/
├── app.py
├── pipeline.py
├── config/
│   └── .env.example
├── module/
│   ├── transcribe.py
│   ├── translate.py
│   └── tts.py
├── outputs/
├── uploads/
├── web/
│   ├── index.html
│   ├── script.js
│   └── style.css
└── requirements.txt
```

### What belongs where

- `app.py` — edge routing, file handling, and high-level HTTP orchestration.
- `pipeline.py` — business logic orchestration and data normalization.
- `module/transcribe.py` — low-level speech recognition adapter.
- `module/translate.py` — translation adapter.
- `module/tts.py` — speech generation adapter.
- `web/` — browser-facing UI and static assets.
- `outputs/` — generated deliverables.
- `uploads/` — incoming temporary source files.

---

## Code Examples and Structural Patterns

### `app.py` route example

```python
@app.route('/api/dub', methods=['POST'])
def dub_audio():
    if 'audioFile' not in request.files:
        return jsonify({'error': 'Missing audioFile field.'}), 400

    uploaded_file = request.files['audioFile']
    if uploaded_file.filename == '':
        return jsonify({'error': 'No file selected.'}), 400

    if not allowed_file(uploaded_file.filename):
        return jsonify({'error': 'Unsupported file type.'}), 400

    filename = secure_filename(uploaded_file.filename)
    session_id = uuid.uuid4().hex
    saved_filename = f"{session_id}_{filename}"
    saved_path = UPLOAD_DIR / saved_filename
    uploaded_file.save(saved_path)

    src_lang = request.form.get('srcLang', DEFAULT_SRC_LANG)
    tgt_lang = request.form.get('tgtLang', DEFAULT_TGT_LANG)
    voice_clone = request.form.get('voiceClone') == 'on'
    voice_method = request.form.get('voiceMethod')
    if voice_method == 'auto':
        voice_method = None

    output_format = request.form.get('outputFormat', 'wav').lower()
    output_format = output_format if output_format in OUTPUT_FORMATS else 'wav'
    enhance_audio = request.form.get('enhanceAudio') == 'on'

    try:
        if is_video_file(saved_filename):
            audio_source = extract_audio_from_video(saved_path, UPLOAD_DIR / f"{session_id}_source.wav")
        else:
            audio_source = saved_path

        if enhance_audio:
            enhanced_audio = UPLOAD_DIR / f"{session_id}_enhanced.wav"
            audio_source = enhance_audio_file(audio_source, enhanced_audio)

        pipeline = AudioTranslationPipeline(src_lang=src_lang, tgt_lang=tgt_lang, voice_method=voice_method)
        output_filename = f"{session_id}_dubbed.{output_format}"
        output_path = OUTPUT_DIR / output_filename
        result = pipeline.run(str(audio_source), str(output_path))

        response = {
            'audioUrl': f'/outputs/{output_filename}',
            'translatedText': result.get('translated_text', ''),
            'translatedSegments': result.get('translated_segments', []),
            'segments': result.get('segments', []),
            'isVideo': is_video_file(saved_filename),
            'sourceFile': filename,
            'sourceLang': src_lang,
            'targetLang': tgt_lang,
            'voiceClone': voice_clone,
            'voiceMethod': voice_method or 'auto',
            'enhanceAudio': enhance_audio,
        }

        if is_video_file(saved_filename):
            dubbed_video_filename = f"{session_id}_dubbed.mp4"
            dubbed_video_path = OUTPUT_DIR / dubbed_video_filename
            replace_audio_in_video(saved_path, output_path, dubbed_video_path)
            response['videoUrl'] = f'/outputs/{dubbed_video_filename}'

        return jsonify(response)
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500
```

### `pipeline.py` segment translation

```python
for segment in segments:
    seg_text = segment.get('text', '')
    translated = self.translate(seg_text) if seg_text else ''
    translated_segments.append({
        'start': segment.get('start'),
        'end': segment.get('end'),
        'text': seg_text,
        'translated': translated,
    })

# Build a continuous TTS payload without losing spoken intent.
tts_text = ' '.join(s['translated'] for s in translated_segments if s.get('translated'))
```

### Frontend segment rendering

```js
function renderResults(result) {
    if (result.translatedSegments && result.translatedSegments.length) {
        const lines = result.translatedSegments.map(s => {
            const start = (typeof s.start === 'number') ? s.start.toFixed(2) : s.start;
            const end = (typeof s.end === 'number') ? s.end.toFixed(2) : s.end;
            const text = s.translated || s.text || '';
            return `[${start} - ${end}] ${text}`;
        });
        translatedText.textContent = lines.join('\n');
    } else {
        translatedText.textContent = result.translatedText || 'No translated transcript available.';
    }
}
```

---

## Best Practices

### Commit habits

- Keep environment secrets out of Git.
- Use descriptive commit messages for new features and fixes.
- Document API additions in this README.

### Code quality

- Keep business logic in `pipeline.py`, not `app.py`.
- Keep provider-specific details in `module/`.
- Keep frontend JS behavior in `web/script.js` and styling in `web/style.css`.

### Security considerations

- Validate uploaded filenames
- Use `secure_filename` from `werkzeug`
- Sanitize user-provided data before using it in paths or shell commands
- Never store API keys in source control

---

## Customization and Built-in Extensibility

### Adding new languages

The source and target selectors in `web/index.html` can be expanded with additional language options. The backend is designed to accept any language code supported by the translation provider.

### Enabling advanced audio filters

`enhance_audio_file` can be updated to add noise reduction, equalization, or adaptive loudness presets.

### Supporting subtitle export

The `translated_segments` array already contains the required timing metadata to generate SRT/VTT output.

### Structured transcript export

A future extension can easily write JSON, Markdown, or subtitle files from `translated_segments` without changing the existing pipeline contract.

---

## Troubleshooting Reference

### Check upload folder permissions

The application writes to `uploads/` and `outputs/`. Ensure your process has write permissions in these directories.

### Validate environment variables

Missing `ELEVENLABS_API_KEY` or incorrect `GOOGLE_APPLICATION_CREDENTIALS` will cause provider-specific TTS failures.

### Reproduce locally

Run the server and try uploading a known-good short audio file first to confirm the pipeline is healthy.

---

## Performance Considerations

### Recommended hardware

- Small workloads: CPU-only environments work fine.
- Heavy transcription loads: GPUs with CUDA support drastically reduce inference time.
- Production video dubbing: use FFmpeg-friendly servers with reserved disk space.

### Model sizing

`faster-whisper` supports several model sizes. Use smaller models for faster iteration and larger models for higher transcription accuracy.

---

## Security and Compliance

- Keep all API keys in `.env`
- Do not commit `config/.env`
- Use HTTPS when deploying in production
- Sanitize all user input before running external binaries
- Log only non-sensitive processing metadata

---

## Glossary

- **Dubbing** — replacing the original audio with a new voice track.
- **Transcription** — converting spoken audio into text.
- **Translation** — converting text from one language to another.
- **TTS** — text-to-speech, synthesizing spoken audio from text.
- **Lip-sync** — aligning dubbed audio to the existing video stream.
- **Segment** — a portion of speech with a timestamp range.

---

## License

This project is distributed under a permissive license. Use it for reference, experimentation, or as the foundation for a production dubbing workflow.

---

## Appendix A — Development checklist

- [x] Clean upload and output directories
- [x] Comprehensive route validation
- [x] Per-segment translation output
- [x] Audio enhancement option
- [x] Video dubbing support
- [x] Responsive studio UI
- [x] Downloadable assets
- [x] Modular transcription / translation / TTS adapters
- [x] Full pipeline orchestration

## Appendix B — Example project commands

```powershell
# Create virtual environment and install dependencies
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Run locally
python app.py

# Run pipeline manually
python pipeline.py uploads/source.wav outputs/dubbed.mp3 --src-lang es --tgt-lang en --transcript outputs/transcript.txt
```

---

## Appendix C — Common extension points

- `module/transcribe.py` — swap Whisper for another ASR engine
- `module/translate.py` — add third-party translator adapters
- `module/tts.py` — add custom voice or vector-based synthesis
- `app.py` — add authentication, rate limiting, or job queues
- `web/` — add user accounts, file history, and project dashboards

---

## Contact and Contribution

If you are iterating on this repository, keep the following in mind:

- Use feature branches
- Keep backend changes compartmentalized
- Add README documentation for every new workflow
- Validate UI changes across desktop and mobile widths
- Test audio and video outputs manually after pipeline changes

Thank you for using AI Dubbing Studio.

# AI Dubbing Studio

A professional-level AI dubbing product built with:
- Flask backend API
- Faster Whisper transcription
- Deep Translator for text translation
- Multi-engine TTS support (ElevenLabs, Coqui, Google Cloud, fallback gTTS)
- FFmpeg audio/video processing for dubbing and lip-sync output
- Modern web UI with responsive controls, progress tracking, and download-ready results

## Features

- Upload audio or video files
- Select source and target languages
- Choose output format (WAV or MP3)
- Enable audio enhancement for clarity and normalization
- Enable voice cloning behavior
- Generate dubbed video output by replacing the audio track
- View translated transcript and download files

## Getting Started

1. Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

2. Copy configuration example:

```powershell
copy .\config\.env.example .\config\.env
```

3. Update `.\config\.env` with API keys and model settings.

4. Install FFmpeg and ensure it is available on your system `PATH`.

5. Run the app:

```powershell
python app.py
```

6. Open `http://127.0.0.1:5000` in your browser.

## Notes

- `Faster-Whisper` requires a model download and may use CPU or GPU depending on `WHISPER_DEVICE`.
- Google Cloud TTS requires a service account JSON file and the `GOOGLE_APPLICATION_CREDENTIALS` environment variable.
- ElevenLabs requires a valid `ELEVENLABS_API_KEY`.
- Video output generation depends on FFmpeg being installed.

## File Structure

- `app.py` — Flask API and file handling
- `pipeline.py` — transcription, translation and synthesis orchestration
- `module/` — individual implementation modules
- `web/` — frontend UI, styles, and client logic
- `outputs/` — generated audio and video assets
- `config/.env.example` — sample environment variables

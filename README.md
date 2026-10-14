# AI Dubbing Studio

Beta commercial application for automated video and audio localization.

AI Dubbing Studio converts source media into a dubbed version in another language while preserving the original speaker identity and timing as closely as possible. The workflow covers transcription, translation, voice generation, and final media rendering in a single process.

## Product overview

- Input: audio or video files
- Process: transcription, translation, voice synthesis, and media reassembly
- Output: dubbed audio, translated transcript, and final video when applicable
- Use case: localization for content teams, media publishers, and multilingual distribution

## Workflow

```text
Upload source media
      |
      v
Extract audio (video only)
      |
      v
Transcribe with timestamps
      |
      v
Translate by segment
      |
      v
Generate translated voice in source voice profile
      |
      v
Rebuild final audio/video
      |
      v
Deliver downloadable outputs
```

## Core capabilities

- Speech-to-text transcription with timing data
- Segment-level translation for natural pacing
- Voice cloning to preserve the original speaker's sound
- Video reassembly with the dubbed audio track
- Downloadable transcript and final output files

## System architecture

```text
Browser / Client
       |
       v
API layer (FastAPI)
       |
       +--> Storage (R2)
       |
       +--> Processing pipeline
               |
               +--> WhisperX for transcription
               +--> Groq for translation
               +--> Zonos-2 for voice generation
               +--> FFmpeg for media handling

Final outputs are returned to the application and made available for download.
```

## Technical stack

- WhisperX: transcription and alignment
- Groq: translation
- Zonos-2: voice cloning and speech generation
- FFmpeg: audio and video processing
- FastAPI: backend orchestration
- Cloud storage + worker pipeline: job handling and delivery

## Commercial beta status

This project is a beta commercial application. It is intended for controlled production evaluation, deployment, and operational use, with outputs suitable for teams that require a practical dubbing workflow without a manual editing pipeline.

## Delivered output

- Dubbed audio file
- Translated transcript
- Final dubbed video (when the source is video)
- Download links provided through the application workflow

## Notes

This repository is structured for a managed product workflow rather than as a local-run developer guide. The platform is intended to support repeatable, production-oriented localization work in a controlled deployment environment.

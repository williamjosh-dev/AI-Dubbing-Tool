import os
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from pipeline import AudioTranslationPipeline

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
UPLOAD_DIR = ROOT_DIR / "uploads"
OUTPUT_DIR = ROOT_DIR / "outputs"
FFMPEG_PATH = os.getenv("FFMPEG_PATH", "ffmpeg")

ALLOWED_EXTENSIONS = {"mp3", "wav", "ogg", "flac", "m4a", "mp4", "mov", "avi", "mkv", "webm"}
VIDEO_EXTENSIONS = {"mp4", "mov", "avi", "mkv", "webm"}
AUDIO_OUTPUT_FORMATS = {"wav", "mp3"}

LANGUAGE_ALIASES = {
    "english": "en",
    "en": "en",
    "spanish": "es",
    "es": "es",
    "french": "fr",
    "fr": "fr",
    "german": "de",
    "de": "de",
    "hindi": "hi",
    "hi": "hi",
    "arabic": "ar",
    "ar": "ar",
    "portuguese": "pt",
    "pt": "pt",
    "japanese": "ja",
    "ja": "ja",
}

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="AI Dubbing API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/outputs", StaticFiles(directory=str(OUTPUT_DIR)), name="outputs")


def normalize_language(value: str, default: str) -> str:
    normalized = (value or "").strip().lower()
    if not normalized:
        return default
    return LANGUAGE_ALIASES.get(normalized, normalized)


def normalize_output_format(value: str) -> str:
    normalized = (value or "").strip().lower()
    if normalized not in AUDIO_OUTPUT_FORMATS:
        raise HTTPException(status_code=400, detail="outputFormat must be 'wav' or 'mp3'.")
    return normalized


def is_video_file(filename: str) -> bool:
    if "." not in filename:
        return False
    return filename.rsplit(".", 1)[1].lower() in VIDEO_EXTENSIONS


def has_allowed_extension(filename: str) -> bool:
    if "." not in filename:
        return False
    return filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def parse_flag(value: str) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def is_ffmpeg_available() -> bool:
    return shutil.which(FFMPEG_PATH) is not None


def run_ffmpeg(command: list[str]) -> None:
    try:
        subprocess.run(command, check=True, capture_output=True)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail="FFmpeg is required but was not found on PATH.") from exc
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.decode("utf-8", errors="ignore").strip() if exc.stderr else ""
        stdout = exc.stdout.decode("utf-8", errors="ignore").strip() if exc.stdout else ""
        message = stderr or stdout or str(exc)
        raise HTTPException(status_code=500, detail=f"FFmpeg processing failed: {message}") from exc


def extract_audio(source_path: Path, target_path: Path, enhance_audio: bool) -> None:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        FFMPEG_PATH,
        "-y",
        "-i",
        str(source_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
    ]
    if enhance_audio:
        command += ["-af", "loudnorm=I=-16:TP=-1.5:LRA=11"]
    command.append(str(target_path))
    run_ffmpeg(command)


def replace_audio_in_video(video_path: Path, audio_path: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        FFMPEG_PATH,
        "-y",
        "-i",
        str(video_path),
        "-i",
        str(audio_path),
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-shortest",
        str(output_path),
    ]
    run_ffmpeg(command)


@app.get("/api/health")
def health_check() -> dict:
    return {"ok": True, "ffmpegAvailable": is_ffmpeg_available()}


@app.post("/api/dub")
def dub_audio(
    audioFile: UploadFile = File(...),
    srcLang: str = Form("en"),
    tgtLang: str = Form("es"),
    voiceClone: str = Form("off"),
    voiceMethod: Optional[str] = Form(None),
    outputFormat: str = Form("wav"),
    enhanceAudio: str = Form("off"),
) -> dict:
    if not audioFile.filename:
        raise HTTPException(status_code=400, detail="A file name is required.")

    if not is_ffmpeg_available():
        raise HTTPException(
            status_code=503,
            detail="FFmpeg is required for video/audio uploads but was not found on PATH.",
        )

    if not has_allowed_extension(audioFile.filename):
        raise HTTPException(status_code=400, detail="Unsupported file type.")

    job_id = uuid.uuid4().hex[:12]
    original_ext = audioFile.filename.rsplit(".", 1)[1].lower()
    safe_stem = Path(audioFile.filename).stem.replace(" ", "_")
    source_path = UPLOAD_DIR / f"{job_id}_{safe_stem}.{original_ext}"

    with source_path.open("wb") as buffer:
        shutil.copyfileobj(audioFile.file, buffer)

    is_video = is_video_file(audioFile.filename)
    source_language = normalize_language(srcLang, "en")
    target_language = normalize_language(tgtLang, "es")
    output_format = normalize_output_format(outputFormat)
    enhance_flag = parse_flag(enhanceAudio)
    voice_method = (voiceMethod or "").strip().lower() or None

    warnings = []
    if parse_flag(voiceClone):
        warnings.append("Voice cloning is not enabled yet; using the selected TTS engine instead.")

    working_audio_path = OUTPUT_DIR / f"{job_id}_input.wav"
    dubbed_audio_path = OUTPUT_DIR / f"{job_id}_dubbed.{output_format}"
    transcript_path = OUTPUT_DIR / f"{job_id}_transcript.txt"
    dubbed_video_path = OUTPUT_DIR / f"{job_id}_dubbed.mp4"

    try:
        extract_audio(source_path, working_audio_path, enhance_flag)

        pipeline = AudioTranslationPipeline(
            src_lang=source_language,
            tgt_lang=target_language,
            voice_method=voice_method,
        )

        pipeline_result = pipeline.run(
            audio_path=str(working_audio_path),
            output_audio_path=str(dubbed_audio_path),
            transcript_path=str(transcript_path),
            save_translated_text=True,
        )

        response = {
            "jobId": job_id,
            "isVideo": is_video,
            "sourceLanguage": source_language,
            "targetLanguage": target_language,
            "voiceMethod": voice_method or "auto",
            "outputFormat": output_format,
            "audioUrl": f"/outputs/{dubbed_audio_path.name}",
            "transcriptUrl": f"/outputs/{transcript_path.name}",
            "translatedText": pipeline_result["translated_text"],
            "translatedSegments": pipeline_result["translated_segments"],
            "warnings": warnings,
        }

        if is_video:
            replace_audio_in_video(source_path, dubbed_audio_path, dubbed_video_path)
            response["videoUrl"] = f"/outputs/{dubbed_video_path.name}"

        return response

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        try:
            audioFile.file.close()
        except Exception:
            pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=5000)

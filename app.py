import os
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from pipeline import AudioTranslationPipeline

# Configuration
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"

ALLOWED_EXTENSIONS = {
    "mp3", "wav", "ogg", "flac", "m4a",
    "mp4", "mov", "avi", "mkv", "webm",
}
VIDEO_EXTENSIONS = {"mp4", "mov", "avi", "mkv", "webm"}
OUTPUT_FORMATS = {"wav", "mp3"}
DEFAULT_SRC_LANG = "es"
DEFAULT_TGT_LANG = "en"

# Initialization
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="AI Dubbing API")

# CORS configuration for Next.js (usually runs on port 3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins like ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file serving for outputs
app.mount("/outputs", StaticFiles(directory=str(OUTPUT_DIR)), name="outputs")

# Helper functions
def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def is_video_file(filename: str) -> bool:
    return filename.rsplit(".", 1)[1].lower() in VIDEO_EXTENSIONS

def run_ffmpeg(command: List[str]) -> None:
    completed = subprocess.run(command, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {completed.stderr.strip()}")

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
    if not audio_path.exists() or audio_path.stat().st_size == 0:
        raise RuntimeError("Audio extraction produced no output")
    return audio_path

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
    if not output_path.exists() or output_path.stat().st_size == 0:
        raise RuntimeError("Audio enhancement produced no output")
    return output_path

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
    if not output_video_path.exists() or output_video_path.stat().st_size == 0:
        raise RuntimeError("Dubbed video generation failed")
    return output_video_path

# API Routes
@app.get("/")
def read_root():
    return {"message": "AI Dubbing API is running. Visit /docs for documentation."}

@app.post("/api/dub")
def dub_audio(
    audioFile: UploadFile = File(...),
    srcLang: str = Form(DEFAULT_SRC_LANG),
    tgtLang: str = Form(DEFAULT_TGT_LANG),
    voiceClone: str = Form("off"),
    voiceMethod: Optional[str] = Form(None),
    outputFormat: str = Form("wav"),
    enhanceAudio: str = Form("off")
):
    if not allowed_file(audioFile.filename):
        raise HTTPException(status_code=400, detail="Unsupported file type.")

    session_id = uuid.uuid4().hex
    filename = audioFile.filename
    saved_filename = f"{session_id}_{filename}"
    saved_path = UPLOAD_DIR / saved_filename

    with open(saved_path, "wb") as buffer:
        shutil.copyfileobj(audioFile.file, buffer)

    # Process parameters
    is_voice_clone = voiceClone == "on"
    if voiceMethod == "auto":
        voice_method = None
    else:
        voice_method = voiceMethod
    
    out_format = outputFormat.lower() if outputFormat.lower() in OUTPUT_FORMATS else "wav"
    is_enhance = enhanceAudio == "on"

    try:
        if is_video_file(saved_filename):
            audio_source = extract_audio_from_video(saved_path, UPLOAD_DIR / f"{session_id}_source.wav")
        else:
            audio_source = saved_path

        if is_enhance:
            enhanced_audio = UPLOAD_DIR / f"{session_id}_enhanced.wav"
            audio_source = enhance_audio_file(audio_source, enhanced_audio)

        pipeline = AudioTranslationPipeline(src_lang=srcLang, tgt_lang=tgtLang, voice_method=voice_method)
        output_filename = f"{session_id}_dubbed.{out_format}"
        output_path = OUTPUT_DIR / output_filename
        
        result = pipeline.run(str(audio_source), str(output_path))

        response = {
            "audioUrl": f"/outputs/{output_filename}",
            "translatedText": result.get("translated_text", ""),
            "translatedSegments": result.get("translated_segments", []),
            "segments": result.get("segments", []),
            "isVideo": is_video_file(saved_filename),
            "sourceFile": filename,
            "sourceLang": srcLang,
            "targetLang": tgtLang,
            "voiceClone": is_voice_clone,
            "voiceMethod": voice_method or "auto",
            "enhanceAudio": is_enhance,
        }

        if is_video_file(saved_filename):
            dubbed_video_filename = f"{session_id}_dubbed.mp4"
            dubbed_video_path = OUTPUT_DIR / dubbed_video_filename
            replace_audio_in_video(saved_path, output_path, dubbed_video_path)
            response["videoUrl"] = f"/outputs/{dubbed_video_filename}"

        return response

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)

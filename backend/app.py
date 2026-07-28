import os
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pipeline import AudioTranslationPipeline

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"

ALLOWED_EXTENSIONS = {"mp3", "wav", "ogg", "flac", "m4a", "mp4", "mov", "avi", "mkv", "webm"}
VIDEO_EXTENSIONS = {"mp4", "mov", "avi", "mkv", "webm"}
OUTPUT_FORMATS = {"wav", "mp3"}

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="AI Dubbing API")

# Crucial for Next.js cross-origin connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], # Your Next.js local port location
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/outputs", StaticFiles(directory=str(OUTPUT_DIR)), name="outputs")

def is_video_file(filename: str) -> bool:
    return filename.rsplit(".", 1)[1].lower() in VIDEO_EXTENSIONS

# ... (Keep your helper functions extract_audio, enhance_audio, replace_audio here exactly as they are)

@app.post("/api/dub")
def dub_audio(
    audioFile: UploadFile = File(...),
    srcLang: str = Form("es"),
    tgtLang: str = Form("en"),
    voiceClone: str = Form("off"),
    voiceMethod: Optional[str] = Form(None),
    outputFormat: str = Form("wav"),
    enhanceAudio: str = Form("off")
):
    # ... (Keep your exact API try/except processing logic block here)
    pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5000)

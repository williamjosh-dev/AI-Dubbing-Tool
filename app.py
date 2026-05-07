#!/usr/bin/env python3
import os
import shutil
import subprocess
import uuid
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename

from pipeline import AudioTranslationPipeline

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"
WEB_DIR = BASE_DIR / "web"

ALLOWED_EXTENSIONS = {
    "mp3", "wav", "ogg", "flac", "m4a",
    "mp4", "mov", "avi", "mkv", "webm",
}
VIDEO_EXTENSIONS = {"mp4", "mov", "avi", "mkv", "webm"}

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__, static_folder=str(WEB_DIR), static_url_path="")


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def is_video_file(filename: str) -> bool:
    return filename.rsplit(".", 1)[1].lower() in VIDEO_EXTENSIONS


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

    completed = subprocess.run(command, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(f"Audio extraction failed: {completed.stderr.strip()}")

    if not audio_path.exists() or audio_path.stat().st_size == 0:
        raise RuntimeError("Audio extraction produced no output")

    return audio_path


@app.route("/")
def index():
    return app.send_static_file("index.html")


@app.route("/api/dub", methods=["POST"])
def dub_audio():
    if "audioFile" not in request.files:
        return jsonify({"error": "Missing audioFile field."}), 400

    uploaded_file = request.files["audioFile"]
    if uploaded_file.filename == "":
        return jsonify({"error": "No file selected."}), 400

    if not allowed_file(uploaded_file.filename):
        return jsonify({"error": "Unsupported file type."}), 400

    filename = secure_filename(uploaded_file.filename)
    session_id = uuid.uuid4().hex
    saved_filename = f"{session_id}_{filename}"
    saved_path = UPLOAD_DIR / saved_filename
    uploaded_file.save(saved_path)

    voice_clone = request.form.get("voiceClone") == "on"
    voice_method = request.form.get("voiceMethod") if voice_clone else None

    try:
        if is_video_file(saved_filename):
            audio_source = extract_audio_from_video(saved_path, UPLOAD_DIR / f"{session_id}_audio.wav")
        else:
            audio_source = saved_path

        pipeline = AudioTranslationPipeline(src_lang="es", tgt_lang="en", voice_method=voice_method)
        output_filename = f"{session_id}_dubbed.wav"
        output_path = OUTPUT_DIR / output_filename
        result = pipeline.run(str(audio_source), str(output_path))

        return jsonify({
            "audioUrl": f"/outputs/{output_filename}",
            "translatedText": result.get("translated_text", ""),
            "segments": result.get("segments", []),
            "isVideo": is_video_file(saved_filename),
        })

    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/outputs/<path:filename>")
def serve_output(filename: str):
    return send_from_directory(OUTPUT_DIR, filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

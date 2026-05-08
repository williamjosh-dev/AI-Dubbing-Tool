#!/usr/bin/env python3
import os
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import List

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
OUTPUT_FORMATS = {"wav", "mp3"}
DEFAULT_SRC_LANG = "es"
DEFAULT_TGT_LANG = "en"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__, static_folder=str(WEB_DIR), static_url_path="")


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

    src_lang = request.form.get("srcLang", DEFAULT_SRC_LANG)
    tgt_lang = request.form.get("tgtLang", DEFAULT_TGT_LANG)
    voice_clone = request.form.get("voiceClone") == "on"
    voice_method = request.form.get("voiceMethod")
    if voice_method == "auto":
        voice_method = None
    output_format = request.form.get("outputFormat", "wav").lower()
    output_format = output_format if output_format in OUTPUT_FORMATS else "wav"
    enhance_audio = request.form.get("enhanceAudio") == "on"

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
            "audioUrl": f"/outputs/{output_filename}",
            "translatedText": result.get("translated_text", ""),
            "segments": result.get("segments", []),
            "isVideo": is_video_file(saved_filename),
            "sourceFile": filename,
            "sourceLang": src_lang,
            "targetLang": tgt_lang,
            "voiceClone": voice_clone,
            "voiceMethod": voice_method or "auto",
            "enhanceAudio": enhance_audio,
        }

        if is_video_file(saved_filename):
            dubbed_video_filename = f"{session_id}_dubbed.mp4"
            dubbed_video_path = OUTPUT_DIR / dubbed_video_filename
            replace_audio_in_video(saved_path, output_path, dubbed_video_path)
            response["videoUrl"] = f"/outputs/{dubbed_video_filename}"

        return jsonify(response)

    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/outputs/<path:filename>")
def serve_output(filename: str):
    return send_from_directory(OUTPUT_DIR, filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

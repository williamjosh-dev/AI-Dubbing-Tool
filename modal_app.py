import os
import sys
import tempfile
from pathlib import Path

import modal

ROOT_DIR = Path(__file__).parent
MODEL_VOLUME = modal.Volume.from_name("ai-models-cache", create_if_missing=True)
MODEL_CACHE_DIR = "/root/model_cache"

# ==========================================
# 1. CPU IMAGE (Orchestration & API)
# ==========================================
cpu_image = (
    modal.Image.debian_slim(python_version="3.11")
    .add_local_dir(ROOT_DIR / "backend", remote_path="/root/backend")
    .add_local_file(ROOT_DIR / "modal_app.py", remote_path="/root/modal_app.py")
    .apt_install("ffmpeg")
    .pip_install(
        "fastapi[standard]",
        "groq",
        "pydub",
        "python-dotenv>=1.0",
        "requests",
        "modal",
    )
)

# ==========================================
# 2. WHISPERX GPU IMAGE (T4 Worker)
# ==========================================
whisperx_image = (
    modal.Image.from_registry(
        "nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04", add_python="3.11"
    )
    .add_local_dir(ROOT_DIR / "backend", remote_path="/root/backend")
    .add_local_file(ROOT_DIR / "modal_app.py", remote_path="/root/modal_app.py")
    .apt_install("ffmpeg", "git")
    .pip_install(
        "torch==2.4.1",
        "torchaudio==2.4.1",
        "git+https://github.com/m-bain/whisperX.git",
        "python-dotenv>=1.0",
    )
)

# ==========================================
# 3. ZONOS GPU IMAGE (L4 Worker)
# ==========================================
zonos_image = (
    modal.Image.from_registry(
        "nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04", add_python="3.11"
    )
    .add_local_dir(ROOT_DIR / "backend", remote_path="/root/backend")
    # Added espeak-ng (mandatory for phonemization)
    .apt_install("git", "ffmpeg", "espeak-ng")
    .pip_install(
        "torch==2.4.1",
        "torchaudio==2.4.1",
        "huggingface_hub[hf_transfer]",
        "requests",
        "python-dotenv>=1.0",
        "soundfile",
    )
    .run_commands(
        "git clone https://github.com/Zyphra/Zonos2.git /root/Zonos2",
        "cd /root/Zonos2 && pip install -e .",
    )
    .env(
        {
            "HF_HUB_ENABLE_HF_TRANSFER": "1",
            "HF_HOME": f"{MODEL_CACHE_DIR}/huggingface",
        }
    )
)

app = modal.App("ai-dubbing-full-pipeline")


@app.function(
    image=whisperx_image,
    gpu="T4",
    volumes={MODEL_CACHE_DIR: MODEL_VOLUME},
    timeout=900,
)
def whisperx_worker(audio_bytes: bytes, language: str) -> list[dict]:
    """Transcribe one audio payload on a T4 worker."""
    sys.path.insert(0, "/root/backend")
    from backend.module.transcribe import transcribe_audio

    with tempfile.NamedTemporaryFile(suffix=".wav") as source:
        source.write(audio_bytes)
        source.flush()
        return transcribe_audio(source.name, language=language)


@app.function(
    image=zonos_image,
    gpu="L4",
    volumes={MODEL_CACHE_DIR: MODEL_VOLUME},
    secrets=[modal.Secret.from_name("my-groq-secret")],
    timeout=900,
)
def zonos_worker(text: str, reference_audio_bytes: bytes, language: str) -> bytes:
    """Synthesize one translated segment on an L4 worker."""
    sys.path.insert(0, "/root/backend")
    from backend.module.tts import generate_speech

    with tempfile.TemporaryDirectory() as temp_dir:
        reference_path = os.path.join(temp_dir, "reference.wav")
        output_path = os.path.join(temp_dir, "segment.wav")
        with open(reference_path, "wb") as reference:
            reference.write(reference_audio_bytes)
        generate_speech(
            text,
            output_path,
            reference_audio=reference_path,
            language=language,
        )
        with open(output_path, "rb") as generated:
            return generated.read()


@app.function(
    image=cpu_image,
    secrets=[modal.Secret.from_name("my-groq-secret")],
    timeout=900,
)
@modal.asgi_app()
def fastapi_app():
    """Serve upload, FFmpeg, translation, and output assembly on CPU."""
    sys.path.insert(0, "/root")
    sys.path.insert(0, "/root/backend")
    os.environ.setdefault("DUBBING_USE_MODAL_WORKERS", "1")

    from backend.app import app as local_fastapi_app

    return local_fastapi_app
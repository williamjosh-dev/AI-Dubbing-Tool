import os
import sys
import tempfile
import subprocess
import requests
from pathlib import Path

import modal

ROOT_DIR = Path(__file__).parent
MODEL_VOLUME = modal.Volume.from_name("ai-models-cache", create_if_missing=True)
SHARED_VOLUME = modal.Volume.from_name("dubbing-shared-storage", create_if_missing=True)

MODEL_CACHE_DIR = "/root/model_cache"
STORAGE_DIR = "/root/shared_storage"

# ==========================================
# 1. CPU IMAGE (Container 1: Orchestration, FFmpeg, Supabase Storage)
# ==========================================
cpu_image = (
    modal.Image.debian_slim(python_version="3.11")
    .add_local_dir(ROOT_DIR / "backend", remote_path="/root/backend")
    .add_local_file(ROOT_DIR / "modal_app.py", remote_path="/root/modal_app.py")
    .apt_install("ffmpeg", "libavcodec-extra")
    .pip_install(
        "fastapi[standard]",
        "groq",
        "pydub",
        "python-dotenv>=1.0",
        "requests",
        "modal",
        "supabase",
        "sqlalchemy>=2.0",
        "psycopg2-binary",
    )
)

# ==========================================
# 2. WHISPERX GPU IMAGE (Container 2: T4 Worker)
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
        "groq",
        "python-dotenv>=1.0",
    )
)

# ==========================================
# 3. ZONOS GPU IMAGE (Container 3: L4 Worker)
# ==========================================
zonos_image = (
    modal.Image.from_registry(
        "nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04", add_python="3.11"
    )
    .add_local_dir(ROOT_DIR / "backend", remote_path="/root/backend")
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
        "pip install /root/Zonos2",
    )
    .env(
        {
            "HF_HUB_ENABLE_HF_TRANSFER": "1",
            "HF_HOME": f"{MODEL_CACHE_DIR}/huggingface",
        }
    )
)

app = modal.App("ai-dubbing-full-pipeline")


# -------------------------------------------------------------
# STEP 1: Container 1 [CPU] - Extract Audio via FFmpeg
# -------------------------------------------------------------
@app.function(image=cpu_image, volumes={STORAGE_DIR: SHARED_VOLUME}, timeout=300)
def extract_audio_container(job_id: str, video_path: str) -> str:
    try:
        job_dir = os.path.join(STORAGE_DIR, job_id)
        os.makedirs(job_dir, exist_ok=True)
        extracted_wav = os.path.join(job_dir, "extracted.wav")

        cmd = [
            "ffmpeg", "-y", "-i", video_path,
            "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
            extracted_wav
        ]
        result = subprocess.run(cmd, capture_output=True, check=False, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg audio extraction failed: {result.stderr}")
        SHARED_VOLUME.commit()
        return extracted_wav
    except Exception as e:
        print(f"ERROR [extract_audio_container]: {str(e)}")
        raise


# -------------------------------------------------------------
# STEP 2: Container 2 [T4 GPU] - WhisperX / Groq API Call
# -------------------------------------------------------------
@app.function(
    image=whisperx_image,
    gpu="T4",
    volumes={MODEL_CACHE_DIR: MODEL_VOLUME, STORAGE_DIR: SHARED_VOLUME},
    secrets=[modal.Secret.from_name("my-repo-secrets")],
    timeout=600,
)
def transcribe_container(audio_path: str, src_lang: str) -> list[dict]:
    try:
        sys.path.insert(0, "/root")
        from backend.module.transcribe import transcribe_audio

        # Handles Groq API call with automatic WhisperX local fallback
        return transcribe_audio(audio_path, language=src_lang)
    except Exception as e:
        print(f"ERROR [transcribe_container]: {str(e)}")
        raise


# -------------------------------------------------------------
# STEP 3: Container 3 [L4 GPU] - Zonos-v2 Voice Cloning
# -------------------------------------------------------------
@app.function(
    image=zonos_image,
    gpu="L4",
    volumes={MODEL_CACHE_DIR: MODEL_VOLUME, STORAGE_DIR: SHARED_VOLUME},
    timeout=600,
)
def synthesize_container(text: str, ref_audio_path: str, out_path: str, tgt_lang: str) -> str:
    try:
        sys.path.insert(0, "/root/backend")
        from backend.module.tts import generate_speech

        generate_speech(
            text=text,
            output_path=out_path,
            reference_audio=ref_audio_path,
            language=tgt_lang,
        )
        SHARED_VOLUME.commit()
        return out_path
    except Exception as e:
        print(f"ERROR [synthesize_container]: {str(e)}")
        raise


@app.function(
    image=zonos_image,
    gpu="L4",
    volumes={MODEL_CACHE_DIR: MODEL_VOLUME, STORAGE_DIR: SHARED_VOLUME},
    timeout=600,
)
def zonos_worker(text: str, reference_audio: bytes | None, tgt_lang: str) -> bytes:
    """Synthesize one segment for the backend pipeline and return WAV bytes."""
    sys.path.insert(0, "/root/backend")
    from backend.module.tts import generate_speech

    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir) / "segment.wav"
        reference_path = None
        if reference_audio:
            reference_path = Path(temp_dir) / "reference.wav"
            reference_path.write_bytes(reference_audio)

        generate_speech(
            text=text,
            output_path=str(output_path),
            reference_audio=str(reference_path) if reference_path else None,
            language=tgt_lang,
        )
        return output_path.read_bytes()


# -------------------------------------------------------------
# STEP 4: Container 1 [CPU] - Time-Stretch, Merge, Supabase Storage & Ping
# -------------------------------------------------------------
@app.function(
    image=cpu_image,
    volumes={STORAGE_DIR: SHARED_VOLUME},
    secrets=[modal.Secret.from_name("my-repo-secrets")],
    timeout=900,
)
def assemble_and_finish_container(
    job_id: str,
    original_video_path: str,
    translated_segments: list[dict],
    webhook_url: str
):
    from pydub import AudioSegment
    sys.path.insert(0, "/root")
    from backend.storage import upload_public_file

    job_dir = os.path.join(STORAGE_DIR, job_id)
    final_audio_path = os.path.join(job_dir, "dubbed_timeline.wav")
    final_video_path = os.path.join(job_dir, "final_dubbed.mp4")

    # 1. Timeline Assembly with FFmpeg `atempo` Time-Stretching
    base_audio = AudioSegment.from_file(original_video_path)
    timeline = AudioSegment.silent(duration=len(base_audio))

    for i, seg in enumerate(translated_segments):
        raw_seg_file = os.path.join(job_dir, f"raw_seg_{i}.wav")
        if not os.path.exists(raw_seg_file):
            continue

        target_dur_ms = int((seg["end"] - seg["start"]) * 1000)
        seg_audio = AudioSegment.from_file(raw_seg_file)
        actual_dur_ms = len(seg_audio)

        # Apply FFmpeg atempo filter if segment exceeds window length
        stretched_file = os.path.join(job_dir, f"stretched_seg_{i}.wav")
        if actual_dur_ms > target_dur_ms and target_dur_ms > 100:
            speed_ratio = round(actual_dur_ms / target_dur_ms, 2)
            speed_ratio = min(speed_ratio, 1.35)  # Cap speed factor for natural voice
            
            cmd = [
                "ffmpeg", "-y", "-i", raw_seg_file,
                "-filter:a", f"atempo={speed_ratio}",
                stretched_file
            ]
            result = subprocess.run(cmd, capture_output=True, check=False, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg atempo failed: {result.stderr}")
            processed_clip = AudioSegment.from_file(stretched_file)
        else:
            processed_clip = seg_audio

        timeline = timeline.overlay(processed_clip, position=int(seg["start"] * 1000))

    timeline.export(final_audio_path, format="wav")

    # 2. Merge Dubbed Audio with Original Video
    cmd_merge = [
        "ffmpeg", "-y",
        "-i", original_video_path,
        "-i", final_audio_path,
        "-c:v", "copy",
        "-map", "0:v:0",
        "-map", "1:a:0",
        final_video_path
    ]
    result = subprocess.run(cmd_merge, capture_output=True, check=False, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg merge failed: {result.stderr}")

    # 3. Upload the final output to public Supabase Storage.
    try:
        public_url = upload_public_file(Path(final_video_path), job_id, "video")
    except Exception as e:
        raise RuntimeError(f"Supabase Storage upload failed: {str(e)}")

    # 4. Webhook Ping Back to Vercel
    if webhook_url:
        try:
            requests.post(
                webhook_url,
                json={
                    "job_id": job_id,
                    "status": "COMPLETED",
                    "download_url": public_url
                },
                timeout=10
            )
        except Exception as e:
            # Log webhook error but don't fail the job
            print(f"Warning: Webhook notification failed: {str(e)}")

    return public_url


def call_assemble_and_finish(
    job_id: str,
    original_video_path: str,
    translated_segments: list[dict],
    webhook_url: str = "",
) -> str:
    """Call the Modal assembler for files stored on the shared Modal volume."""
    if not Path(original_video_path).is_file():
        raise FileNotFoundError(f"Original video not found: {original_video_path}")
    if not translated_segments:
        raise ValueError("At least one translated segment is required.")

    return assemble_and_finish_container.remote(
        job_id,
        original_video_path,
        translated_segments,
        webhook_url,
    )


# -------------------------------------------------------------
# MODAL ORCHESTRATOR: Async Pipeline Trigger
# -------------------------------------------------------------
@app.function(
    image=cpu_image,
    volumes={STORAGE_DIR: SHARED_VOLUME},
    secrets=[modal.Secret.from_name("my-repo-secrets")],
    timeout=900,
)
@modal.asgi_app()
def fastapi_app():
    sys.path.insert(0, "/root")
    sys.path.insert(0, "/root/backend")
    os.environ.setdefault("DUBBING_USE_MODAL_WORKERS", "1")

    from backend.app import app as local_fastapi_app
    return local_fastapi_app

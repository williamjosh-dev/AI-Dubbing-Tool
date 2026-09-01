import gc
import os
import subprocess
import sys
from pathlib import Path

import modal
import requests

ROOT_DIR = Path(__file__).parent
MODEL_VOLUME = modal.Volume.from_name("ai-models-cache", create_if_missing=True)
SHARED_VOLUME = modal.Volume.from_name("dubbing-shared-storage", create_if_missing=True)

MODEL_CACHE_DIR = "/root/model_cache"
STORAGE_DIR = "/root/shared_storage"

# ==========================================
# 1. CPU IMAGE
# ==========================================
cpu_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("ffmpeg", "libavcodec-extra")
    .pip_install(
        "fastapi[standard]",
        "groq",
        "numpy<2.0.0",
        "protobuf>=5.0.0",
        "pydub",
        "python-dotenv>=1.0",
        "requests",
        "modal",
        "supabase",
        "sqlalchemy>=2.0",
        "psycopg2-binary",
        "deep-translator",
    )
    .add_local_dir(ROOT_DIR / "backend", remote_path="/root/backend")
)

# ==========================================
# 2. L4 GPU IMAGE
# ==========================================
def download_demucs_weights():
    from demucs.pretrained import get_model
    get_model("htdemucs")

l4_image = (
    modal.Image.from_registry(
        "nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04", add_python="3.11"
    )
    .apt_install(
        "ffmpeg",
        "git",
        "espeak-ng",
        "libfst-dev",
        "build-essential"
    )
    .pip_install(
        "numpy<2.0.0",
        "torch==2.4.0",
        "torchaudio==2.4.0",
        "ctranslate2>=4.4.0",
        "faster-whisper>=1.0.3",
        "transformers>=4.40.0,<4.48.0",
        "huggingface_hub",
        "soundfile",
        "pydub",
        "pyannote.audio>=3.1.1",
        "omegaconf>=2.3.0",
        "pandas>=2.2.0",
        "nltk>=3.9.1",
        "groq",
        "protobuf>=5.0.0",
        "python-dotenv>=1.0",
        "msgpack",
        "ninja>=1.11.0",
        "sacremoses>=0.1.1",
        "demucs",
    )
    .run_commands(
        "pip install --no-deps git+https://github.com/m-bain/whisperX.git",
        "git clone https://github.com/Zyphra/Zonos2.git /root/Zonos2",
        "pip install --no-deps descript-audio-codec==1.0.0",
        "pip install /root/Zonos2 --no-deps"
    )
    .run_function(download_demucs_weights)
    .env(
        {
            "HF_HOME": f"{MODEL_CACHE_DIR}/huggingface",
            "TORCH_HOME": f"{MODEL_CACHE_DIR}/torch",
            "XDG_CACHE_HOME": f"{MODEL_CACHE_DIR}/cache",
            "HF_HUB_ENABLE_HF_TRANSFER": "1",
            "WHISPER_MODEL": "large-v3",
            "WHISPER_BATCH_SIZE": "4",
            "WHISPER_COMPUTE_TYPE": "float16",
        }
    )
    .add_local_dir(ROOT_DIR / "backend", remote_path="/root/backend")
)

app = modal.App("ai-dubbing-full-pipeline")

# -------------------------------------------------------------
# STEP 1: CPU Worker - Audio Extraction
# -------------------------------------------------------------
@app.function(image=cpu_image, volumes={STORAGE_DIR: SHARED_VOLUME}, timeout=300)
def extract_audio_container(job_id: str, video_path: str) -> str:
    if "/root" not in sys.path:
        sys.path.insert(0, "/root")

    # Clean inputs and strip null bytes
    job_id = str(job_id).replace("\x00", "").strip()
    video_path = str(video_path).replace("\x00", "").strip()

    # Safety check against passing file contents instead of file paths
    if len(video_path) > 1024:
        raise ValueError(
            f"video_path is unusually long ({len(video_path)} chars). "
            "Ensure you are passing a file path, not raw binary/base64 data."
        )

    SHARED_VOLUME.reload()
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


# -------------------------------------------------------------
# STEP 2: L4 GPU Worker Pipeline
# -------------------------------------------------------------
@app.function(
    image=l4_image,
    gpu="L4",
    max_containers=1,
    volumes={MODEL_CACHE_DIR: MODEL_VOLUME, STORAGE_DIR: SHARED_VOLUME},
    secrets=[modal.Secret.from_name("my-repo-secrets")],
    timeout=1800,
)
def process_gpu_pipeline(
    audio_path: str,
    job_id: str,
    src_lang: str,
    tgt_lang: str,
    separate_stems: bool = True,
) -> list[dict]:
    import torch
    from pydub import AudioSegment

    SHARED_VOLUME.reload()
    import sys
    if "/root" not in sys.path:
        sys.path.insert(0, "/root")

    from backend.demucs_service import DemucsBackend
    from backend.module.transcribe import transcribe_audio_whisperx_full
    from backend.module.translate import translate_text
    from backend.module.tts import generate_speech

    job_dir = Path(STORAGE_DIR) / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    vocals_path = str(job_dir / "isolated_vocals.wav")
    background_path = str(job_dir / "background_track.wav")
    target_transcription_audio = audio_path

    # Demucs Source Separation
    if separate_stems:
        print(f"[{job_id}] Demucs Separation")
        demucs_worker = DemucsBackend(model_name="htdemucs", device="cuda")
        with open(audio_path, "rb") as f:
            raw_audio_bytes = f.read()

        stems = demucs_worker.separate_stems(raw_audio_bytes, stems=["vocals", "no_vocals"])

        with open(vocals_path, "wb") as f:
            f.write(stems["vocals"])
        with open(background_path, "wb") as f:
            f.write(stems["no_vocals"])

        target_transcription_audio = vocals_path
        SHARED_VOLUME.commit()

        del demucs_worker
        gc.collect()
        torch.cuda.empty_cache()

    # WhisperX Transcription
    print(f"[{job_id}] WhisperX Transcription")
    segments = transcribe_audio_whisperx_full(
        target_transcription_audio,
        src_lang,
        device="cuda",
        model_name="large-v3",
        compute_type=os.getenv("WHISPER_COMPUTE_TYPE", "float16"),
        batch_size=int(os.getenv("WHISPER_BATCH_SIZE", "4")),
    )
    if not segments:
        raise RuntimeError("WhisperX returned no speech segments")

    MODEL_VOLUME.commit()
    gc.collect()
    torch.cuda.empty_cache()

    # Translation
    print(f"[{job_id}] Translation ({len(segments)} segments)")
    translated_segments = []
    for segment in segments:
        text = segment.get("text", "").strip()
        translated_segments.append({
            **segment,
            "translated": translate_text(text, src_lang, tgt_lang) if text else "",
        })

    # Zonos Voice Cloning
    print(f"[{job_id}] Zonos Voice Cloning")
    ref_source_path = vocals_path if separate_stems and os.path.exists(vocals_path) else audio_path
    source_audio = AudioSegment.from_file(ref_source_path)
    audio_duration_ms = len(source_audio)

    for index, segment in enumerate(translated_segments):
        translated_text = segment.get("translated", "").strip()
        if not translated_text:
            continue

        start_ms = min(audio_duration_ms, max(0, int(segment.get("start", 0) * 1000)))
        end_ms = min(audio_duration_ms, max(start_ms + 100, int(segment.get("end", 0) * 1000)))
        
        reference_path = job_dir / f"ref_{index}.wav"
        output_path = job_dir / f"raw_seg_{index}.wav"
        
        source_audio[start_ms:end_ms].export(reference_path, format="wav")
        generate_speech(
            text=translated_text,
            output_path=str(output_path),
            reference_audio=str(reference_path),
            language=tgt_lang,
        )

    SHARED_VOLUME.commit()
    return translated_segments

# -------------------------------------------------------------
# STEP 3: Time-Stretch & Assembly
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
    webhook_url: str = "",
    is_video: bool = True,
    output_format: str = "wav",
) -> dict:
    from pydub import AudioSegment
    if "/root" not in sys.path:
        sys.path.insert(0, "/root")
    from backend.storage import upload_public_file

    SHARED_VOLUME.reload()
    job_dir = os.path.join(STORAGE_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)
    
    final_audio_path = os.path.join(job_dir, f"dubbed_timeline.{output_format}")
    final_video_path = os.path.join(job_dir, "final_dubbed.mp4")

    background_path = os.path.join(job_dir, "background_track.wav")
    base_audio = AudioSegment.from_file(background_path if os.path.exists(background_path) else original_video_path)

    timeline = AudioSegment.silent(duration=len(base_audio)).overlay(base_audio)

    for i, seg in enumerate(translated_segments):
        raw_seg_file = os.path.join(job_dir, f"raw_seg_{i}.wav")
        if not os.path.exists(raw_seg_file):
            continue

        target_dur_ms = int((seg["end"] - seg["start"]) * 1000)
        seg_audio = AudioSegment.from_file(raw_seg_file)
        actual_dur_ms = len(seg_audio)

        stretched_file = os.path.join(job_dir, f"stretched_seg_{i}.wav")
        if actual_dur_ms > target_dur_ms and target_dur_ms > 100:
            speed_ratio = round(actual_dur_ms / target_dur_ms, 2)
            # Safe clamping for FFmpeg atempo (must be between 0.5 and 2.0)
            speed_ratio = max(0.5, min(speed_ratio, 1.4))
            
            cmd = [
                "ffmpeg", "-y", "-i", raw_seg_file,
                "-filter:a", f"atempo={speed_ratio}",
                stretched_file
            ]
            result = subprocess.run(cmd, capture_output=True, check=False, text=True)
            processed_clip = AudioSegment.from_file(stretched_file) if result.returncode == 0 else seg_audio
        else:
            processed_clip = seg_audio

        timeline = timeline.overlay(processed_clip, position=int(seg["start"] * 1000))

    timeline.export(final_audio_path, format=output_format)

    if is_video:
        cmd_merge = [
            "ffmpeg", "-y",
            "-i", original_video_path,
            "-i", final_audio_path,
            "-c:v", "copy",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-c:a", "aac",
            "-shortest",
            final_video_path,
        ]
        result = subprocess.run(cmd_merge, capture_output=True, check=False, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg merge failed: {result.stderr}")

    audio_url = upload_public_file(Path(final_audio_path), job_id, "audio")
    video_url = upload_public_file(Path(final_video_path), job_id, "video") if is_video else None
    public_url = video_url or audio_url

    if webhook_url:
        try:
            requests.post(
                webhook_url,
                json={"job_id": job_id, "status": "COMPLETED", "download_url": public_url},
                timeout=10,
            )
        except Exception as e:
            print(f"Webhook failed: {e}")

    SHARED_VOLUME.commit()
    return {"audio_url": audio_url, "video_url": video_url, "download_url": public_url}

# -------------------------------------------------------------
# STEP 4: Main Orchestrator Function
# -------------------------------------------------------------
@app.function(
    image=cpu_image,
    volumes={STORAGE_DIR: SHARED_VOLUME},
    secrets=[modal.Secret.from_name("my-repo-secrets")],
    timeout=1800,
)
def run_modal_job(
    job_id: str,
    source_path: str,
    is_video: bool,
    source_language: str,
    target_language: str,
    output_format: str,
    enhance_audio: bool,
    *args,  # Catch-all for extra positional arguments to prevent TypeError
    **kwargs,
) -> dict:
    if "/root" not in sys.path:
        sys.path.insert(0, "/root")
    from backend.db import Job, SessionLocal
    from backend.storage import upload_public_file

    job_dir = Path(STORAGE_DIR) / job_id
    SHARED_VOLUME.reload()
    db = SessionLocal()
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job:
        db.close()
        raise RuntimeError(f"Job not found: {job_id}")

    try:
        job.status = "processing"
        db.commit()

        # Invocations via .remote()
        working_audio_path = extract_audio_container.remote(job_id, source_path)
        
        translated_segments = process_gpu_pipeline.remote(
            working_audio_path,
            job_id,
            source_language,
            target_language,
            separate_stems=enhance_audio,
        )

        transcript_path = job_dir / f"{job_id}_transcript.txt"
        transcript_path.write_text(
            "\n".join(
                f"[{segment['start']:.3f} - {segment['end']:.3f}] "
                f"{segment.get('text', '')} -> {segment.get('translated', '')}"
                for segment in translated_segments
            ),
            encoding="utf-8",
        )
        SHARED_VOLUME.commit()

        result = assemble_and_finish_container.remote(
            job_id, source_path, translated_segments, "", is_video, output_format
        )
        job.audio_url = result["audio_url"]
        job.video_url = result["video_url"]
        job.download_url = result["download_url"]
        job.transcript_url = upload_public_file(transcript_path, job_id, "transcript")
        job.status = "completed"
        db.commit()
        return {
            "audioUrl": job.audio_url,
            "videoUrl": job.video_url,
            "transcriptUrl": job.transcript_url,
        }
    except Exception as exc:
        db.rollback()
        job.status = "failed"
        job.error = str(exc)[:500]
        db.commit()
        raise
    finally:
        db.close()

@app.function(
    image=cpu_image,
    volumes={STORAGE_DIR: SHARED_VOLUME},
    secrets=[modal.Secret.from_name("my-repo-secrets")],
    timeout=900,
)
@modal.asgi_app()
def fastapi_app():
    if "/root" not in sys.path:
        sys.path.insert(0, "/root")
    os.environ.setdefault("DUBBING_USE_MODAL_WORKERS", "1")
    os.environ.setdefault("MODAL_PIPELINE", "1")

    from backend.app import app as local_fastapi_app
    return local_fastapi_app

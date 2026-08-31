import os
import sys
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
# 1. CPU IMAGE (Container 1: Orchestration, FFmpeg, Supabase)
# ==========================================
cpu_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("ffmpeg", "libavcodec-extra")
    .pip_install(
        "fastapi[standard]",
        "groq",
        "numpy",
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
# 2. L4 GPU IMAGE (WhisperX + Zonos2 Container)
# ==========================================
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
        "torch==2.4.0",
        "torchaudio==2.4.0",
        "ctranslate2>=4.4.0",
        "faster-whisper>=1.0.3",
        "transformers>=4.40.0,<4.48.0",
        "huggingface_hub",
        "soundfile",
        "pydub",
        "numpy<2.0.0",
        "pyannote.audio>=3.1.1",
        "omegaconf>=2.3.0",
        "pandas>=2.2.0",
        "nltk>=3.9.1",
        "groq",
        "protobuf>=5.0.0",
        "python-dotenv>=1.0",
        "msgpack",
        "ninja>=1.11.0",
        "sacremoses>=0.1.1"
    )
    .run_commands(
        "pip install --no-deps git+https://github.com/m-bain/whisperX.git",
        "git clone https://github.com/Zyphra/Zonos2.git /root/Zonos2",
        "pip install --no-deps descript-audio-codec==1.0.0",
        "pip install /root/Zonos2 --no-deps"
    )
    .env(
        {
            "HF_HOME": f"{MODEL_CACHE_DIR}/huggingface",
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
    try:
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
        
        # Explicit Commit to ensure L4 GPU container can read extracted.wav
        SHARED_VOLUME.commit()
        return extracted_wav
    except Exception as e:
        print(f"ERROR [extract_audio_container]: {str(e)}")
        raise


# -------------------------------------------------------------
# STEP 2: L4 GPU Worker - Transcription, Translation, TTS
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
) -> list[dict]:
    try:
        from pydub import AudioSegment

        # Sync Shared Storage to access extracted.wav from Container 1
        SHARED_VOLUME.reload()

        if "/root" not in sys.path:
            sys.path.insert(0, "/root")

        from backend.module.transcribe import transcribe_audio_whisperx_full
        from backend.module.translate import translate_text
        from backend.module.tts import generate_speech

        print(f"[{job_id}] 1/3 WhisperX transcription & alignment (large-v3)")
        
        segments = transcribe_audio_whisperx_full(
            audio_path,
            src_lang,
            device="cuda",
            model_name="large-v3",
            compute_type=os.getenv("WHISPER_COMPUTE_TYPE", "float16"),
            batch_size=int(os.getenv("WHISPER_BATCH_SIZE", "4")),
        )
        if not segments:
            raise RuntimeError("WhisperX returned no speech segments")

        # Save downloaded models to volume cache
        MODEL_VOLUME.commit()

        print(f"[{job_id}] 2/3 Translation ({len(segments)} segments)")
        translated_segments = []
        for segment in segments:
            text = segment.get("text", "").strip()
            translated_segments.append({
                **segment,
                "translated": translate_text(text, src_lang, tgt_lang) if text else "",
            })

        print(f"[{job_id}] 3/3 Zonos Voice Cloning ({len(translated_segments)} segments)")
        source_audio = AudioSegment.from_file(audio_path)
        job_dir = Path(STORAGE_DIR) / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        for index, segment in enumerate(translated_segments):
            translated_text = segment.get("translated", "").strip()
            if not translated_text:
                continue

            start_ms = max(0, int(segment.get("start", 0) * 1000))
            end_ms = max(start_ms + 100, int(segment.get("end", 0) * 1000))
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
    except Exception as e:
        print(f"ERROR [process_gpu_pipeline]: {str(e)}")
        raise


# -------------------------------------------------------------
# STEP 3: CPU Worker - Time-Stretch, Merge & Storage Upload
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
    final_audio_path = os.path.join(job_dir, f"dubbed_timeline.{output_format}")
    final_video_path = os.path.join(job_dir, "final_dubbed.mp4")

    # 1. Timeline Assembly with Safe FFmpeg `atempo` Filter
    base_audio = AudioSegment.from_file(original_video_path)
    timeline = AudioSegment.silent(duration=len(base_audio))

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
            # Cap speed ratio at 1.4 for natural listening
            speed_ratio = min(speed_ratio, 1.4)
            
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

    # 2. Merge audio back into original video
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

    # 3. Upload artifacts to Supabase Storage
    try:
        audio_url = upload_public_file(Path(final_audio_path), job_id, "audio")
        video_url = upload_public_file(Path(final_video_path), job_id, "video") if is_video else None
    except Exception as e:
        raise RuntimeError(f"Supabase Storage upload failed: {str(e)}")

    public_url = video_url or audio_url

    # 4. Optional Webhook Trigger
    if webhook_url:
        try:
            requests.post(
                webhook_url,
                json={
                    "job_id": job_id,
                    "status": "COMPLETED",
                    "download_url": public_url,
                    "audio_url": audio_url,
                    "video_url": video_url,
                },
                timeout=10
            )
        except Exception as e:
            print(f"Warning: Webhook notification failed: {str(e)}")

    SHARED_VOLUME.commit()
    return {"audio_url": audio_url, "video_url": video_url, "download_url": public_url}


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

        working_audio_path = extract_audio_container.remote(job_id, source_path)
        
        translated_segments = process_gpu_pipeline.remote(
            working_audio_path,
            job_id,
            source_language,
            target_language,
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


# -------------------------------------------------------------
# MODAL ASGI Web App Entrypoint
# -------------------------------------------------------------
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
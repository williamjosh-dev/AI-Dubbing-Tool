"""
Hybrid Transcriber Module:
- Attempts Groq Cloud API (whisper-large-v3) for fast initial transcription.
- Uses local WhisperX (wav2vec2) for precise forced word/character alignment.
- Falls back to full local WhisperX pipeline if Groq is unavailable or fails.
"""

import gc
import os
from typing import Any, Dict, List

import torch
import whisperx
from dotenv import load_dotenv
from groq import Groq

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "config", ".env"))

groq_api_key = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=groq_api_key) if groq_api_key else None


def align_with_whisperx(
    audio_file_path: str,
    segments: List[Dict[str, Any]],
    language: str,
    device: str = "cuda",
) -> List[Dict[str, Any]]:
    """Applies Wav2Vec2 forced alignment to pre-transcribed text segments.
    
    Bypasses initial Whisper transcription step for speed.
    """
    if not segments:
        return segments

    print(f"⏱️ Aligning transcript with WhisperX wav2vec2 model ({language}) on {device}...")

    # Sanitize segments for WhisperX aligner requirements
    cleaned_segments = []
    for seg in segments:
        raw_text = seg.get("text", "").strip()
        if raw_text:
            cleaned_segments.append(
                {
                    "start": float(seg.get("start", 0.0)),
                    "end": float(seg.get("end", 0.0)),
                    "text": raw_text,
                }
            )

    if not cleaned_segments:
        return segments

    align_model = None
    try:
        audio = whisperx.load_audio(audio_file_path)
        align_model, metadata = whisperx.load_align_model(
            language_code=language, device=device
        )

        aligned_result = whisperx.align(
            cleaned_segments,
            align_model,
            metadata,
            audio,
            device,
            return_char_alignments=False,
        )
        return aligned_result.get("segments", cleaned_segments)

    except Exception as e:
        print(f"⚠️ Forced alignment failed: {e}. Falling back to raw segments.")
        return segments

    finally:
        # Guarantee VRAM release even if alignment raises an Exception
        if align_model is not None:
            del align_model
        gc.collect()
        if device == "cuda" and torch.cuda.is_available():
            torch.cuda.empty_cache()


def transcribe_audio_whisperx_full(
    audio_path: str,
    language: str = "en",
    device: str = "cuda",
    model_name: str = "large-v3",
    compute_type: str = "float16",
    batch_size: int = 4,
) -> List[Dict[str, Any]]:
    """Full local WhisperX pipeline (Transcription + Forced Alignment)."""
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    target_model = model_name or os.getenv("WHISPER_MODEL", "large-v3")
    print(f"🎙️ Running local WhisperX transcription [{target_model}] on {device}...")

    model = None
    try:
        audio = whisperx.load_audio(audio_path)
        model = whisperx.load_model(
            target_model,
            device=device,
            compute_type=compute_type,
            language=language,
        )
        result = model.transcribe(audio, batch_size=batch_size)
        raw_segments = result.get("segments", [])

    finally:
        if model is not None:
            del model
        gc.collect()
        if device == "cuda" and torch.cuda.is_available():
            torch.cuda.empty_cache()

    return align_with_whisperx(audio_path, raw_segments, language, device)


def transcribe_audio(
    audio_path: str, language: str = "es", enable_alignment: bool = True
) -> List[Dict[str, Any]]:
    """Hybrid Transcriber: Attempts Groq API first; falls back to local WhisperX."""
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    language = (language or "es").strip().lower()
    device = os.getenv("WHISPER_DEVICE", "cuda" if torch.cuda.is_available() else "cpu")
    compute_type = os.getenv("WHISPER_COMPUTE_TYPE", "float16" if device == "cuda" else "int8")
    batch_size = int(os.getenv("WHISPER_BATCH_SIZE", "4"))

    segments: List[Dict[str, Any]] = []
    used_groq = False

    # 1. Primary Route: Groq Cloud API
    if groq_client:
        try:
            file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
            if file_size_mb > 24.5:
                print(f"⚠️ File size ({file_size_mb:.1f}MB) exceeds Groq limit. Using local WhisperX.")
            else:
                print("🚀 Fetching transcript from Groq API (whisper-large-v3)...")
                with open(audio_path, "rb") as file:
                    response = groq_client.audio.transcriptions.create(
                        file=(os.path.basename(audio_path), file.read()),
                        model="whisper-large-v3",
                        language=language,
                        response_format="verbose_json",
                        timestamp_granularities=["segment"],
                    )

                raw_segments = getattr(response, "segments", [])
                for seg in raw_segments:
                    seg_dict = seg if isinstance(seg, dict) else getattr(seg, "__dict__", {})
                    segments.append(
                        {
                            "start": float(seg_dict.get("start", 0.0)),
                            "end": float(seg_dict.get("end", 0.0)),
                            "text": str(seg_dict.get("text", "")).strip(),
                        }
                    )
                used_groq = True

        except Exception as groq_err:
            print(f"⚠️ Groq API failed ({groq_err}). Switching to local WhisperX...")

    # 2. Forced Alignment / Local Fallback Execution
    if used_groq and segments and enable_alignment:
        segments = align_with_whisperx(audio_path, segments, language, device)

    elif not segments:
        segments = transcribe_audio_whisperx_full(
            audio_path=audio_path,
            language=language,
            device=device,
            model_name=os.getenv("WHISPER_MODEL", "large-v3"),
            compute_type=compute_type,
            batch_size=batch_size,
        )

    if not segments:
        raise RuntimeError("No speech recognized in input audio file.")

    # 3. Format Output Structure for Pipeline
    formatted_output = []
    for segment in segments:
        text = segment.get("text", "").strip()
        if not text:
            continue

        seg_data: Dict[str, Any] = {
            "start": float(round(segment.get("start", 0.0), 3)),
            "end": float(round(segment.get("end", 0.0), 3)),
            "text": text,
        }

        if "words" in segment and isinstance(segment["words"], list):
            seg_data["words"] = [
                {
                    "word": str(w.get("word", "")),
                    "start": (
                        float(round(w["start"], 3)) if w.get("start") is not None else None
                    ),
                    "end": float(round(w["end"], 3)) if w.get("end") is not None else None,
                    "score": float(round(w.get("score", 1.0), 3)),
                }
                for w in segment["words"]
                if isinstance(w, dict) and "word" in w
            ]

        formatted_output.append(seg_data)

    return formatted_output
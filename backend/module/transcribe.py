import os
import gc
import torch
import whisperx
from groq import Groq
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', 'config', '.env'))

groq_api_key = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=groq_api_key) if groq_api_key else None


def align_with_whisperx(audio_file_path: str, segments: list, language: str, device: str = "cuda"):
    """
    Applies Wav2Vec2 forced alignment to pre-transcribed text segments.
    Skips Whisper transcription entirely.
    """
    if not segments:
        return segments

    print(f"⏱️ Aligning transcript with WhisperX wav2vec2 model ({language}) on {device}...")
    audio = whisperx.load_audio(audio_file_path)
    
    align_model, metadata = whisperx.load_align_model(
        language_code=language,
        device=device
    )
    
    aligned_result = whisperx.align(
        segments,
        align_model,
        metadata,
        audio,
        device,
        return_char_alignments=False
    )

    # Free memory immediately
    del align_model
    gc.collect()
    if device == "cuda":
        torch.cuda.empty_cache()

    return aligned_result.get("segments", segments)


def transcribe_audio_whisperx_full(
    audio_path: str,
    language: str = "en",
    device: str = "cuda",
    model_name: str = "large-v3",
    compute_type: str = "float16",
    batch_size: int = 4,
):
    """Full local WhisperX pipeline (Transcription + Forced Alignment)."""
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    audio = whisperx.load_audio(audio_path)
    target_model = model_name or os.getenv("WHISPER_MODEL", "large-v3")
    print(f"🎙️ Running WhisperX local transcription [{target_model}] on {device}...")
    
    model = whisperx.load_model(
        target_model,
        device=device,
        compute_type=compute_type,
        language=language
    )
    result = model.transcribe(audio, batch_size=batch_size)

    # Free local model from VRAM before loading alignment model
    del model
    gc.collect()
    if device == "cuda":
        torch.cuda.empty_cache()

    raw_segments = result.get("segments", [])
    return align_with_whisperx(audio_path, raw_segments, language, device)


def transcribe_audio(audio_path: str, language: str = "es", enable_alignment: bool = True):
    """
    Hybrid Transcriber: Attempts Groq API first; falls back to local WhisperX.
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    language = (language or "es").strip() or "es"
    device = os.getenv("WHISPER_DEVICE", "cuda" if torch.cuda.is_available() else "cpu")
    compute_type = os.getenv("WHISPER_COMPUTE_TYPE", "float16" if device == "cuda" else "int8")
    batch_size = int(os.getenv("WHISPER_BATCH_SIZE", "4"))

    segments = []
    used_groq = False

    # 1. Primary Route: Groq API for Fast Text & Basic Segments
    if groq_client:
        try:
            print("🚀 Fetching text from Groq API (whisper-large-v3)...")
            with open(audio_path, "rb") as file:
                response = groq_client.audio.transcriptions.create(
                    file=(os.path.basename(audio_path), file.read()),
                    model="whisper-large-v3",
                    language=language,
                    response_format="verbose_json",
                    timestamp_granularities=["segment"]
                )

            raw_segments = getattr(response, "segments", [])
            for seg in raw_segments:
                seg_dict = seg if isinstance(seg, dict) else seg.__dict__
                segments.append({
                    "start": seg_dict.get("start", 0.0),
                    "end": seg_dict.get("end", 0.0),
                    "text": seg_dict.get("text", "").strip()
                })

            used_groq = True

        except Exception as groq_err:
            print(f"⚠️ Groq API failed ({groq_err}). Switching to local WhisperX...")

    # 2. Alignment Phase / Full Fallback Execution
    if used_groq and segments and enable_alignment:
        try:
            segments = align_with_whisperx(audio_path, segments, language, device)
        except Exception as align_err:
            print(f"⚠️ Hybrid alignment failed ({align_err}). Retaining native Groq timestamps.")

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
        raise RuntimeError("No speech recognized in audio")

    # 3. Format Output Structure
    formatted_output = []
    for segment in segments:
        text = segment.get("text", "").strip()
        if not text:
            continue

        seg_data = {
            "start": float(round(segment.get("start", 0.0), 3)),
            "end": float(round(segment.get("end", 0.0), 3)),
            "text": text,
        }

        if "words" in segment:
            seg_data["words"] = [
                {
                    "word": w.get("word"),
                    "start": float(w["start"]) if w.get("start") is not None else None,
                    "end": float(w["end"]) if w.get("end") is not None else None,
                    "score": float(w.get("score", 1.0)),
                }
                for w in segment["words"]
                if "word" in w
            ]

        formatted_output.append(seg_data)

    return formatted_output

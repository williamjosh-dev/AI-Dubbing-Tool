import os
import gc
import torch
import whisperx
from groq import Groq
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', 'config', '.env'))

groq_api_key = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=groq_api_key) if groq_api_key else None


def align_with_whisperx(audio_file_path, segments, language, device):
    """
    Applies Wav2Vec2 forced alignment to pre-transcribed text segments.
    Skips Whisper transcription entirely.
    """
    if not segments:
        return segments

    print(f"⏱️ Aligning Groq transcript with WhisperX wav2vec2 model ({language})...")
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


def transcribe_audio_whisperx_full(audio_path, language, device, compute_type, batch_size):
    """Fallback handler: Full WhisperX pipeline (Transcription + Alignment)."""
    audio = whisperx.load_audio(audio_path)
    print(f"🎙️ [Fallback] Running full WhisperX local pipeline on {device}...")
    
    model = whisperx.load_model(
        os.getenv("WHISPER_MODEL", "small"),
        device=device,
        compute_type=compute_type,
        language=language
    )
    result = model.transcribe(audio, batch_size=batch_size)

    del model
    gc.collect()
    if device == "cuda":
        torch.cuda.empty_cache()

    segments = result.get("segments", [])
    return align_with_whisperx(audio_path, segments, language, device)


def transcribe_audio(audio_path, language="es", enable_alignment=True):
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    language = (language or "es").strip() or "es"
    device = os.getenv("WHISPER_DEVICE", "cpu")
    compute_type = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
    batch_size = int(os.getenv("WHISPER_BATCH_SIZE", "16"))

    segments = []
    used_groq = False

    # -------------------------------------------------------------
    # 1. Primary Route: Groq API for Fast Text & Basic Segments
    # -------------------------------------------------------------
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

            # Standardize Groq segment structure into WhisperX format
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
            print(f"⚠️ Groq API failed ({groq_err}). Switching to full WhisperX local pipeline...")

    # -------------------------------------------------------------
    # 2. Alignment Phase / Full Fallback Execution
    # -------------------------------------------------------------
    if used_groq and segments and enable_alignment:
        try:
            # HYBRID MODE: Take Groq segments and run WhisperX forced alignment on them
            segments = align_with_whisperx(audio_path, segments, language, device)
        except Exception as align_err:
            print(f"⚠️ Hybrid alignment failed ({align_err}). Keeping native Groq segment timestamps.")

    elif not segments:
        # FULL FALLBACK: Run both transcription and alignment locally with WhisperX
        segments = transcribe_audio_whisperx_full(
            audio_path, language, device, compute_type, batch_size
        )

    if not segments:
        raise RuntimeError("No speech recognized in audio")

    # -------------------------------------------------------------
    # 3. Format Output Structure
    # -------------------------------------------------------------
    formatted_output = []
    for segment in segments:
        text = segment.get("text", "").strip()
        if not text:
            continue

        seg_data = {
            "start": round(segment.get("start", 0.0), 3),
            "end": round(segment.get("end", 0.0), 3),
            "text": text,
        }

        if "words" in segment:
            seg_data["words"] = [
                {
                    "word": w.get("word"),
                    "start": w.get("start"),
                    "end": w.get("end"),
                    "score": w.get("score", 1.0)
                }
                for w in segment["words"]
                if "word" in w
            ]

        formatted_output.append(seg_data)

    return formatted_output

import os
import gc
import torch
import whisperx
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', 'config', '.env'))


def transcribe_audio(audio_path, language="es", enable_alignment=True):
    """
    Transcribe audio file using WhisperX with optional phoneme alignment.
    
    Args:
        audio_path (str): Path to audio file.
        language (str): Source language code (e.g., 'es', 'en').
        enable_alignment (bool): Performs Wav2Vec2 forced alignment for accurate word timestamps.
        
    Returns:
        list: List of dicts containing 'start', 'end', 'text', and optionally 'words'.
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    language = (language or "es").strip() or "es"

    model_name = os.getenv("WHISPER_MODEL", "small")
    device = os.getenv("WHISPER_DEVICE", "cpu")
    compute_type = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
    batch_size = int(os.getenv("WHISPER_BATCH_SIZE", "16"))

    try:
        # 1. Load Audio
        audio = whisperx.load_audio(audio_path)

        # 2. Transcribe with WhisperX
        print(f"🎙️ Loading WhisperX model ({model_name}) on {device}...")
        model = whisperx.load_model(
            model_name,
            device=device,
            compute_type=compute_type,
            language=language
        )

        print("🔄 Transcribing audio...")
        result = model.transcribe(audio, batch_size=batch_size)

        # Free GPU/CPU memory before loading alignment model
        del model
        gc.collect()
        if device == "cuda":
            torch.cuda.empty_cache()

        segments = result.get("segments", [])

        # 3. Optional: Perform Forced Alignment for precise word-level timestamps
        if enable_alignment and segments:
            try:
                print(f"⏱️ Aligning timestamps for language: {language}...")
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
                segments = aligned_result.get("segments", segments)

                # Free alignment model memory
                del align_model
                gc.collect()
                if device == "cuda":
                    torch.cuda.empty_cache()

            except Exception as align_err:
                print(f"⚠️ Alignment failed or model not available for '{language}'. Falling back to raw Whisper timestamps: {align_err}")

    except Exception as e:
        raise RuntimeError(f"WhisperX transcription failed: {e}") from e

    if not segments:
        raise RuntimeError("No speech recognized in audio")

    # Format return output to match your previous return structure
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

        # Include word-level timestamps if alignment succeeded
        if "words" in segment:
            seg_data["words"] = [
                {
                    "word": w.get("word"),
                    "start": w.get("start"),
                    "end": w.get("end"),
                    "score": w.get("score")
                }
                for w in segment["words"]
                if "word" in w
            ]

        formatted_output.append(seg_data)

    return formatted_output

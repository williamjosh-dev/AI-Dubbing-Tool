import os
from dotenv import load_dotenv
from faster_whisper import WhisperModel

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', 'config', '.env'))


def transcribe_audio(audio_path):
    """
    Transcribe audio file to text using faster-whisper (local inference).
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    # Use faster-whisper model names: tiny|base|small|medium|large-v1|large-v2
    # openai/whisper-small can run but sometimes file path model.bin errors occur on Windows.
    model_name = os.getenv("WHISPER_MODEL", "small")
    device = os.getenv("WHISPER_DEVICE", "cpu")

    # Disable HF symlinks on Windows, helps with cache path issues
    # set in PowerShell: $env:HF_HUB_DISABLE_SYMLINKS = "1"
    model = WhisperModel(model_name, device=device, compute_type="int8")

    try:
        segments, _ = model.transcribe(audio_path, language="es", beam_size=5)
    except RuntimeError as e:
        raise RuntimeError(
            "Transcription model load failed. Ensure HF_HUB_DISABLE_SYMLINKS=1 and that model download succeeded. "
            f"Original: {e}"
        ) from e

    if not segments:
        raise RuntimeError("No speech recognized in audio")

    # Return list of segments with start/end and text
    return [
        {
            "start": segment.start,
            "end": segment.end,
            "text": segment.text.strip()
        }
        for segment in segments
        if segment.text.strip()
    ]
"""Zonos2-only voice-cloned speech synthesis."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "config", ".env"))

_zonos_model = None
_speaker_embeddings: dict[str, object] = {}


def _get_zonos_model():
    global _zonos_model

    if _zonos_model is None:
        from zonos2.tts import TTSLLM

        _zonos_model = TTSLLM(model_path=os.getenv("ZONOS2_MODEL", "Zyphra/ZONOS2"))

    return _zonos_model


def generate_speech(
    text: str,
    output_path: str,
    voice_method: str | None = None,
    reference_audio: str | None = None,
    language: str = "en_us",
) -> str:
    """Generate cloned speech with Zonos2 and save it as a WAV file."""
    if not text or not text.strip():
        raise ValueError("No text provided for speech generation")
    if not output_path:
        raise ValueError("No output path provided")
    if not reference_audio or not Path(reference_audio).is_file():
        raise FileNotFoundError("A reference audio file is required for Zonos2 voice cloning")

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.suffix.lower() != ".wav":
        output = output.with_suffix(".wav")

    model = _get_zonos_model()
    reference_key = str(Path(reference_audio).resolve())
    speaker_embedding = _speaker_embeddings.get(reference_key)
    if speaker_embedding is None:
        speaker_embedding = model.embed_speaker_file(reference_audio)
        _speaker_embeddings[reference_key] = speaker_embedding

    from zonos2.message import TTSSamplingParams

    result = model.generate_one(
        text,
        TTSSamplingParams(),
        language=language,
        speaker_embedding=speaker_embedding,
    )
    model.save_audio(result["audio"], str(output))

    if not output.is_file() or output.stat().st_size == 0:
        raise RuntimeError("Zonos2 generated an empty audio file")

    return str(output)

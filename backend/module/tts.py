"""Zonos2-only voice-cloned speech synthesis supporting native languages."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "config", ".env"))

_zonos_model = None
_speaker_embeddings: dict[str, object] = {}

# Zonos2 Language mapping table
LANG_MAP = {
    # Tier 1
    "en": "en_us",
    "en-us": "en_us",
    "en-gb": "en_gb",
    "zh": "cmn",
    "zh-cn": "cmn",
    "ja": "ja",
    # Tier 2
    "es": "es",
    "fr": "fr_fr",
    "de": "de",
    "it": "it",
    "pt": "pt_br",
    "ko": "ko",
    "ru": "ru",
    "nl": "nl",
    # Tier 3 (Indic & others)
    "bn": "bn",
    "hi": "hi",
    "ta": "ta",
    "te": "te",
    "ar": "ar",
    "pl": "pl",
    "uk": "uk",
    "tr": "tr",
}


def _get_zonos_model():
    global _zonos_model

    if _zonos_model is None:
        try:
            from zonos2.tts import TTSLLM

            model_path = os.getenv("ZONOS2_MODEL", "Zyphra/ZONOS2")
            print(f"🔊 Initializing Zonos2 model: {model_path}...")
            _zonos_model = TTSLLM(model_path=model_path)
        except ImportError:
            raise ImportError(
                "Zonos2 library not installed. Make sure Zonos2 is installed in the Modal environment."
            )
        except Exception as e:
            raise RuntimeError(f"Failed to load Zonos2 model: {e}") from e

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
        raise FileNotFoundError(
            f"Reference audio file not found at '{reference_audio}'. Required for Zonos2 voice cloning."
        )

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.suffix.lower() != ".wav":
        output = output.with_suffix(".wav")

    # Normalize language string to Zonos2 format
    raw_lang = (language or "en_us").lower().strip()
    norm_lang = LANG_MAP.get(raw_lang, raw_lang)

    model = _get_zonos_model()
    reference_key = str(Path(reference_audio).resolve())

    # Cache speaker embedding in memory to optimize batch execution
    speaker_embedding = _speaker_embeddings.get(reference_key)
    if speaker_embedding is None:
        print(f"🎙️ Extracting Zonos2 speaker embedding for: {reference_key}")
        speaker_embedding = model.embed_speaker_file(reference_audio)
        _speaker_embeddings[reference_key] = speaker_embedding

    from zonos2.message import TTSSamplingParams

    try:
        # Zonos2 handles native UTF-8 bytes directly
        result = model.generate_one(
            text=text,
            params=TTSSamplingParams(),
            language=norm_lang,
            speaker_embedding=speaker_embedding,
        )
        model.save_audio(result["audio"], str(output))
    except Exception as e:
        raise RuntimeError(f"Zonos2 speech generation failed for text '{text[:20]}...': {e}") from e

    if not output.is_file() or output.stat().st_size == 0:
        raise RuntimeError(f"Zonos2 generated an empty audio file at {output}")

    return str(output)
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', 'config', '.env'))

# Global Client
_groq_client = None

PRIMARY_MODEL = "qwen3.6-27b"       # High-speed, multilingual primary model
FALLBACK_MODEL = "openai/gpt-oss-20b"  # High-rate-limit fallback model

TRANSLATION_PROMPT = """Role: You are an expert natural speech translator.

Task: Translate the input text from source language '{src}' to target language '{tgt}'.

Speech & Audio Constraints:
- Match the length and semantic meaning of the original segment as closely as possible.
- Output ONLY the translated text. Do NOT add commentary, introductions, quotes, or markdown.
- Do NOT add filler words (e.g., "uh," "well," "like") unless present in original text.
- Absolutely NO bullet points, lists, emojis, asterisks, or formatting.
- Spell out numbers, symbols, and currency as plain words (e.g., "one hundred dollars" instead of "$100", "percent" instead of "%")."""


def _get_groq_client():
    """
    Get or create Groq client (singleton pattern).
    """
    global _groq_client

    if _groq_client is None:
        try:
            from groq import Groq

            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY environment variable not set")

            _groq_client = Groq(api_key=api_key)

        except ImportError:
            raise ImportError(
                "Groq SDK not installed. Run: pip install groq"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Groq client: {e}") from e

    return _groq_client


def _call_groq_translation(client, model: str, text: str, src_lang: str, tgt_lang: str) -> str:
    """
    Execute translation via Groq chat completion.
    """
    system_prompt = TRANSLATION_PROMPT.format(src=src_lang, tgt=tgt_lang)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
        temperature=0.2,
    )

    result = response.choices[0].message.content.strip()
    # Strip any accidental wrapping quotes added by LLM
    if (result.startswith('"') and result.endswith('"')) or (result.startswith("'") and result.endswith("'")):
        result = result[1:-1].strip()
    return result


def _fallback_deep_translator(text: str, src_lang: str, tgt_lang: str) -> str:
    """
    Emergency fallback using deep-translator (Google Translate).
    """
    try:
        from deep_translator import GoogleTranslator
        print(f"🌐 Falling back to GoogleTranslator for segment: '{text[:20]}...'")
        translated = GoogleTranslator(source=src_lang, target=tgt_lang).translate(text)
        return translated.strip() if translated else text
    except Exception as e:
        print(f"❌ deep-translator fallback failed: {e}")
        return text


def translate_text(text: str, src_lang: str = "es", tgt_lang: str = "en") -> str:
    """
    Translate text using Groq with Qwen 2.5 32B primary, Llama 3.1 8B fallback,
    and deep-translator emergency fallback.
    """
    if not text or not text.strip():
        return ""

    client = None
    try:
        client = _get_groq_client()
    except Exception as e:
        print(f"⚠️ Groq initialization error: {e}. Falling back to deep-translator...")
        return _fallback_deep_translator(text, src_lang, tgt_lang)

    # Attempt 1: Primary Model (qwen-2.5-32b)
    try:
        return _call_groq_translation(client, PRIMARY_MODEL, text, src_lang, tgt_lang)
    except Exception as e:
        print(f"⚠️ Primary model {PRIMARY_MODEL} failed: {e}")

    # Attempt 2: Fallback Model (Llama-3.1-8b-instant)
    try:
        return _call_groq_translation(client, FALLBACK_MODEL, text, src_lang, tgt_lang)
    except Exception as e:
        print(f"⚠️ Fallback model {FALLBACK_MODEL} failed: {e}")

    # Attempt 3: Free Web Translator Fallback
    return _fallback_deep_translator(text, src_lang, tgt_lang)
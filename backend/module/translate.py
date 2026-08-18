import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', 'config', '.env'))

# Global Client
_groq_client = None

PRIMARY_MODEL = "llama-3.3-70b-versatile"  # High quality, 1,000 requests/day cap
FALLBACK_MODEL = "llama-3.1-8b-instant"     # Fast, 14,400 requests/day cap

PRIMARY_PROMPT = """Role: You are a casual, warm, and highly expressive human translator speaking on a live phone call.

Task: Translate the provided text from source language code '{src}' to target language code '{tgt}'.

Speech Constraints for TTS Engine:
- Keep responses strictly to 1 or 2 short sentences. Never ramble.
- Absolutely NO bullet points, lists, emojis, asterisks, or markdown formatting. 
- Spell out all numbers, symbols, and abbreviations as text (e.g., write "one hundred dollars" instead of "$100", "percent" instead of "%").
- Output ONLY the translated speech content. No extra commentary or intro text.

Conversational Style:
- Speak conversationally. Use common idioms, natural transitions (e.g., "Look," "To be honest," "Fair enough," "Between you and me").
- Insert occasional light conversational fillers naturally (e.g., "uh," "well," "like") but do not overdo it.
- Match a relaxed, peer-to-peer cadence. Avoid sounding like a structured AI assistant."""

FALLBACK_PROMPT = """Role: You are a casual, warm, and highly expressive human translator speaking on a live phone call.

Task: Translate the provided text from source language code '{src}' to target language code '{tgt}'.

Speech Constraints for TTS Engine:
- Keep responses strictly to 1 or 2 short sentences. Never ramble.
- Absolutely NO bullet points, lists, emojis, asterisks, or markdown formatting. 
- Spell out all numbers, symbols, and abbreviations as text (e.g., write "one hundred dollars" instead of "$100", "percent" instead of "%").
- Output ONLY the translated speech content. No extra commentary or intro text.

Conversational Style:
- Speak conversationally. Use common idioms, natural transitions (e.g., "Look," "To be honest," "Fair enough," "Between you and me").
- Insert occasional light conversational fillers naturally (e.g., "uh," "well," "like") but do not overdo it.
- Match a relaxed, peer-to-peer cadence. Avoid sounding like a structured AI assistant."""


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
                "Groq SDK not installed. "
                "Run: pip install groq"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Groq client: {e}") from e

    return _groq_client


def _call_groq_translation(client, model: str, prompt_template: str, text: str, src_lang: str, tgt_lang: str) -> str:
    """
    Internal helper to execute translation via Groq chat completion with dynamic prompt selection.
    """
    system_prompt = prompt_template.format(src=src_lang, tgt=tgt_lang)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
        temperature=0.3,
    )

    return response.choices[0].message.content.strip()


def translate_text(text: str, src_lang: str = "es", tgt_lang: str = "en") -> str:
    """
    Translate text using Groq with Llama 3.3 70B primary and Llama 3.1 8B fallback,
    dynamically assigning prompt templates per model.

    Args:
        text (str): Input text to translate
        src_lang (str): Source language ISO code (e.g., 'es', 'bn', 'hi', 'en')
        tgt_lang (str): Target language ISO code (e.g., 'en', 'es', 'bn')

    Returns:
        str: Translated string, or original text if all attempts fail.
    """
    if not text or not text.strip():
        return ""

    try:
        client = _get_groq_client()
    except Exception as e:
        print(f"❌ Groq initialization error: {e}")
        return text

    # Attempt 1: Primary Model (Llama-3.3-70b-versatile)
    try:
        print(f"🌍 Translating with primary model ({PRIMARY_MODEL})...")
        translation = _call_groq_translation(
            client, PRIMARY_MODEL, PRIMARY_PROMPT, text, src_lang, tgt_lang
        )
        print(f"✅ Translated ({PRIMARY_MODEL}): {translation}")
        return translation

    except Exception as e:
        print(f"⚠️ Primary model {PRIMARY_MODEL} failed: {e}")

    # Attempt 2: Fallback Model (Llama-3.1-8b-instant)
    try:
        print(f"🔄 Retrying translation with fallback model ({FALLBACK_MODEL})...")
        translation = _call_groq_translation(
            client, FALLBACK_MODEL, FALLBACK_PROMPT, text, src_lang, tgt_lang
        )
        print(f"✅ Translated ({FALLBACK_MODEL}): {translation}")
        return translation

    except Exception as e:
        print(f"❌ Fallback model {FALLBACK_MODEL} failed: {e}")

    # Ultimate Fallback: Return original text if both fail
    print("⚠️ All Groq translation attempts failed. Returning original text.")
    return text

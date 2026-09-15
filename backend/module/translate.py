import os
from dotenv import load_dotenv

load_dotenv(
    dotenv_path=os.path.join(
        os.path.dirname(__file__),
        "..",
        "config",
        ".env",
    )
)

# Global client
_groq_client = None

# Groq Compound
MODEL = "groq/compound"

TRANSLATION_PROMPT = """\
Role: You are an expert professional translator specializing in natural spoken
dialogue and dubbing.

Task:
Translate the input from source language '{src}' into target language '{tgt}'.

The translation must sound like something a fluent native speaker would
actually say aloud.

TRANSLATION PRINCIPLES:

- Preserve the exact meaning, intent, context, emotion, and personality of
  the original.
- Translate naturally rather than word-for-word.
- Preserve the speaker's tone and register: casual, formal, sarcastic,
  emotional, angry, humorous, intimate, etc.
- Translate idioms, expressions, metaphors, slang, jokes, and figurative
  language into natural equivalents in the target language whenever possible.
- NEVER translate an idiom literally if the literal version would sound
  unnatural or change its intended meaning.
- Do not invent information that is not present in the original.
- Do not remove meaningful information from the original.
- Resolve ambiguous wording using the surrounding context when possible.
- Preserve names, proper nouns, and terminology unless a natural established
  target-language equivalent is clearly appropriate.

DUBBING / SPOKEN-LANGUAGE RULES:

- Make the result sound natural when spoken aloud.
- Prefer natural spoken phrasing over stiff written phrasing.
- Preserve the original speaker's personality and conversational style.
- Do NOT add filler words such as "uh", "um", "well", "like", etc. unless
  they are present in the original or are genuinely necessary to preserve
  the same conversational effect.
- Do not artificially shorten or expand the translation just to change its
  wording. Stay reasonably close to the original segment's length while
  keeping the translation natural and accurate.
- When several natural translations are possible, prefer the one that is
  easiest and most natural to say aloud.
- Do not turn natural dialogue into textbook or literal translation.

AUDIO / TEXT OUTPUT RULES:

- Output ONLY the translation.
- Do NOT include explanations, notes, analysis, alternatives, or commentary.
- Do NOT include the original text.
- Do NOT add quotation marks around the translation.
- Do NOT add markdown, bullets, numbering, asterisks, emojis, or labels.
- Preserve paragraph or dialogue-segment boundaries when present.
- Spell out numbers, symbols, and currencies in words when appropriate for
  natural speech.
  Example: "$100" -> "one hundred dollars"
  Example: "25%" -> "twenty-five percent"

IMPORTANT:
This is a translation task, NOT a research task.
Do not search the web.
Do not visit websites.
Do not execute code.
Do not use external tools.
Translate the supplied text directly.

Return only the final target-language translation.
"""


def _get_groq_client():
    """
    Get or create the Groq client (singleton pattern).
    """
    global _groq_client

    if _groq_client is None:
        try:
            from groq import Groq

            api_key = os.getenv("GROQ_API_KEY")

            if not api_key:
                raise ValueError(
                    "GROQ_API_KEY environment variable not set"
                )

            # Use the latest Compound system version.
            _groq_client = Groq(
                api_key=api_key,
                default_headers={
                    "Groq-Model-Version": "latest"
                },
            )

        except ImportError:
            raise ImportError(
                "Groq SDK not installed. Run: pip install groq"
            )

        except Exception as e:
            raise RuntimeError(
                f"Failed to initialize Groq client: {e}"
            ) from e

    return _groq_client


def _call_groq_translation(
    client,
    model: str,
    text: str,
    src_lang: str,
    tgt_lang: str,
) -> str:
    """
    Execute direct translation through Groq Compound.

    Compound tools are explicitly disabled because this is a pure
    translation/dubbing task.
    """

    system_prompt = TRANSLATION_PROMPT.format(
        src=src_lang,
        tgt=tgt_lang,
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": text,
            },
        ],

        # Keep translation deterministic and stable.
        temperature=0.2,

        # Preferred current Groq parameter.
        max_completion_tokens=8192,

        # IMPORTANT:
        # Compound normally has access to web/code/etc.
        # Disable all built-in tools for translation.
        compound_custom={
            "tools": {
                "enabled_tools": []
            }
        },
    )

    result = response.choices[0].message.content or ""
    result = result.strip()

    # Remove accidental surrounding quotes only.
    if (
        len(result) >= 2
        and (
            (result.startswith('"') and result.endswith('"'))
            or
            (result.startswith("'") and result.endswith("'"))
        )
    ):
        result = result[1:-1].strip()

    return result


def _fallback_deep_translator(
    text: str,
    src_lang: str,
    tgt_lang: str,
) -> str:
    """
    Emergency fallback using Google Translate through deep-translator.
    """

    try:
        from deep_translator import GoogleTranslator

        print(
            f"🌐 Falling back to GoogleTranslator for segment: "
            f"'{text[:40]}...'"
        )

        translated = GoogleTranslator(
            source=src_lang,
            target=tgt_lang,
        ).translate(text)

        return translated.strip() if translated else text

    except Exception as e:
        print(f"❌ deep-translator fallback failed: {e}")
        return text


def translate_text(
    text: str,
    src_lang: str = "es",
    tgt_lang: str = "en",
) -> str:
    """
    Translate spoken dialogue using Groq Compound.

    Primary:
        groq/compound with all external tools disabled.

    Fallback:
        Google Translate via deep-translator.
    """

    if not text or not text.strip():
        return ""

    try:
        client = _get_groq_client()

    except Exception as e:
        print(
            f"⚠️ Groq initialization error: {e}. "
            "Falling back to deep-translator..."
        )
        return _fallback_deep_translator(
            text,
            src_lang,
            tgt_lang,
        )

    try:
        result = _call_groq_translation(
            client=client,
            model=MODEL,
            text=text,
            src_lang=src_lang,
            tgt_lang=tgt_lang,
        )

        if result:
            return result

        print("⚠️ Groq returned an empty translation.")

    except Exception as e:
        print(
            f"⚠️ Groq Compound translation failed: {e}"
        )

    # Emergency fallback
    return _fallback_deep_translator(
        text,
        src_lang,
        tgt_lang,
    )
import os
import time
from dotenv import load_dotenv

load_dotenv(
    dotenv_path=os.path.join(
        os.path.dirname(__file__),
        "..",
        "config",
        ".env",
    )
)

_groq_client = None

MODEL = "openai/gpt-oss-20b"

# Number of subtitle/dialogue segments sent in one Groq request.
# 15 is a good starting point for dubbing.
BATCH_SIZE = 15

# Safety limit so one request doesn't become enormous.
MAX_BATCH_CHARS = 18000


TRANSLATION_PROMPT = """\
Role: You are an expert professional translator specializing in natural
spoken dialogue and dubbing.

Translate the supplied dialogue segments from '{src}' into '{tgt}'.

The translation must sound like something a fluent native speaker would
actually say aloud.

TRANSLATION RULES:

- Preserve the exact meaning, intent, context, emotion, personality,
  and tone of the original.
- Translate naturally rather than word-for-word.
- Preserve the speaker's register: casual, formal, sarcastic, emotional,
  humorous, angry, intimate, etc.
- Translate idioms, slang, metaphors, jokes, and figurative expressions
  into natural target-language equivalents whenever possible.
- Do NOT translate idioms literally when that would sound unnatural or
  change the intended meaning.
- Do not invent information.
- Do not remove meaningful information.
- Resolve ambiguity using the surrounding dialogue context whenever possible.
- Keep names and proper nouns appropriate to the target language.

DUBBING RULES:

- Make the translation natural when spoken aloud.
- Prefer natural conversational phrasing over stiff written language.
- Preserve the original speaker's personality.
- Do NOT add filler such as "uh", "um", "well", or "like" unless it exists
  in the original or is genuinely required to preserve the same effect.
- Keep each translation reasonably close to the original segment's length,
  but NEVER sacrifice naturalness or meaning just to match length.
- Prefer wording that is easy and natural to say aloud.
- Do not turn dialogue into textbook language.

OUTPUT RULES:

- Return EXACTLY ONE translated segment for every input segment.
- Preserve the segment IDs exactly.
- Do not merge segments.
- Do not split segments.
- Do not skip segments.
- Do not add explanations.
- Do not add alternatives.
- Do not add commentary.
- Do not add markdown.
- Do not add quotation marks.
- Output only the translated segments in the required format.

SEGMENT FORMAT:

<SEGMENT_0001>
translated text
</SEGMENT_0001>

<SEGMENT_0002>
translated text
</SEGMENT_0002>

IMPORTANT:
This is a direct translation task.
Do not search the web.
Do not visit websites.
Do not execute code.
Do not use external tools.

Translate every supplied segment.
"""


def _get_groq_client():
    """Create/reuse the Groq client."""

    global _groq_client

    if _groq_client is None:
        try:
            from groq import Groq

            api_key = os.getenv("GROQ_API_KEY")

            if not api_key:
                raise ValueError(
                    "GROQ_API_KEY environment variable not set"
                )

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


def _build_translation_batch(
    batch,
    src_lang,
    tgt_lang,
):
    """
    Build one prompt containing multiple dialogue segments.
    """

    system_prompt = TRANSLATION_PROMPT.format(
        src=src_lang,
        tgt=tgt_lang,
    )

    parts = []

    for index, segment in enumerate(batch):
        text = segment.get("text", "").strip()

        parts.append(
            f"<SEGMENT_{index:04d}>\n"
            f"{text}\n"
            f"</SEGMENT_{index:04d}>"
        )

    user_prompt = "\n\n".join(parts)

    return system_prompt, user_prompt


def _parse_translation_batch(
    response_text,
    expected_count,
):
    """
    Parse:

    <SEGMENT_0000>
    translation
    </SEGMENT_0000>

    into a list of translations.
    """

    import re

    results = []

    for index in range(expected_count):

        pattern = (
            rf"<SEGMENT_{index:04d}>\s*"
            rf"(.*?)"
            rf"\s*</SEGMENT_{index:04d}>"
        )

        match = re.search(
            pattern,
            response_text,
            flags=re.DOTALL,
        )

        if not match:
            raise ValueError(
                f"Missing translation for SEGMENT_{index:04d}"
            )

        translation = match.group(1).strip()

        if not translation:
            raise ValueError(
                f"Empty translation for SEGMENT_{index:04d}"
            )

        results.append(translation)

    return results


def _call_groq_translation_batch(
    client,
    batch,
    src_lang,
    tgt_lang,
):
    """
    Translate an entire batch in one Groq request.
    """

    system_prompt, user_prompt = _build_translation_batch(
        batch,
        src_lang,
        tgt_lang,
    )

    response = client.chat.completions.create(
        model=MODEL,

        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],

        temperature=0.2,

        # Compound supports large completions.
        # This prevents the old 350-token cap from cutting translations off.
        max_completion_tokens=8192,

        # Translation does not need Compound's agent tools.
        compound_custom={
            "tools": {
                "enabled_tools": []
            }
        },
    )

    result = response.choices[0].message.content or ""

    result = result.strip()

    if not result:
        raise ValueError(
            "Groq returned an empty response."
        )

    return _parse_translation_batch(
        result,
        len(batch),
    )


def _fallback_deep_translator(
    text,
    src_lang,
    tgt_lang,
):
    """
    Emergency single-segment fallback.
    """

    try:
        from deep_translator import GoogleTranslator

        translated = GoogleTranslator(
            source=src_lang,
            target=tgt_lang,
        ).translate(text)

        return translated.strip() if translated else text

    except Exception as e:
        print(
            f"❌ deep-translator fallback failed: {e}"
        )

        return text


def _fallback_batch(
    batch,
    src_lang,
    tgt_lang,
):
    """
    Fallback each segment individually if a Groq batch fails.
    """

    results = []

    for segment in batch:

        text = segment.get("text", "").strip()

        if not text:
            results.append("")
            continue

        results.append(
            _fallback_deep_translator(
                text,
                src_lang,
                tgt_lang,
            )
        )

    return results


def _split_into_batches(
    segments,
    batch_size=BATCH_SIZE,
    max_chars=MAX_BATCH_CHARS,
):
    """
    Split segments into manageable translation batches.

    We consider BOTH:
    - number of segments
    - total character count

    This prevents one giant subtitle segment from making a huge request.
    """

    batches = []
    current = []
    current_chars = 0

    for segment in segments:

        text = segment.get("text", "").strip()
        text_chars = len(text)

        # Empty segments can still travel through the pipeline.
        if not text:
            current.append(segment)
            continue

        would_exceed_chars = (
            current
            and
            current_chars + text_chars > max_chars
        )

        would_exceed_count = (
            current
            and
            len(current) >= batch_size
        )

        if would_exceed_chars or would_exceed_count:
            batches.append(current)

            current = []
            current_chars = 0

        current.append(segment)
        current_chars += text_chars

    if current:
        batches.append(current)

    return batches


def translate_segments(
    segments,
    src_lang="es",
    tgt_lang="en",
):
    """
    Translate all dialogue segments in batches.

    This is the function your dubbing pipeline should call.

    Instead of:

        1 segment = 1 Groq request

    it does approximately:

        15 segments = 1 Groq request
    """

    if not segments:
        return []

    try:
        client = _get_groq_client()

    except Exception as e:
        print(
            f"⚠️ Groq initialization failed: {e}"
        )

        return [
            {
                **segment,
                "translated": (
                    _fallback_deep_translator(
                        segment.get("text", "").strip(),
                        src_lang,
                        tgt_lang,
                    )
                    if segment.get("text", "").strip()
                    else ""
                ),
            }
            for segment in segments
        ]

    batches = _split_into_batches(segments)

    print(
        f"🌐 Translation: "
        f"{len(segments)} segments → "
        f"{len(batches)} Groq requests"
    )

    translated_segments = []

    for batch_number, batch in enumerate(
        batches,
        start=1,
    ):

        print(
            f"   Batch {batch_number}/{len(batches)} "
            f"({len(batch)} segments)"
        )

        try:

            translations = _call_groq_translation_batch(
                client=client,
                batch=batch,
                src_lang=src_lang,
                tgt_lang=tgt_lang,
            )

        except Exception as e:

            print(
                f"⚠️ Groq batch {batch_number} failed: {e}"
            )

            print(
                "   ↳ Falling back to Google Translate "
                "for this batch..."
            )

            translations = _fallback_batch(
                batch,
                src_lang,
                tgt_lang,
            )

        for segment, translation in zip(
            batch,
            translations,
        ):
            translated_segments.append(
                {
                    **segment,
                    "translated": translation,
                }
            )

    return translated_segments


def translate_text(
    text,
    src_lang="es",
    tgt_lang="en",
):
    """
    Compatibility wrapper for code elsewhere that still translates
    a single segment.
    """

    if not text or not text.strip():
        return ""

    segment = {
        "text": text,
    }

    result = translate_segments(
        [segment],
        src_lang,
        tgt_lang,
    )

    return (
        result[0]["translated"]
        if result
        else text
    )
import os
import re

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "config", ".env"))

MODEL = "openai/gpt-oss-20b"
BATCH_SIZE = 5

PROMPT = """Translate the {src} dialogue into natural spoken {tgt}.
Preserve meaning, tone, names, and segment order. Do not explain or add text.
Return exactly one block for every segment using this format:
<SEGMENT_0000>translation</SEGMENT_0000>
"""

_client = None


def _get_client():
    global _client
    if _client is None:
        from groq import Groq

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY is not set")
        _client = Groq(api_key=api_key)
    return _client


def _translate_batch(client, batch, src_lang, tgt_lang):
    prompt = PROMPT.format(src=src_lang, tgt=tgt_lang)
    prompt += "\n\n".join(
        f"<SEGMENT_{i:04d}>{item.get('text', '').strip()}</SEGMENT_{i:04d}>"
        for i, item in enumerate(batch)
    )

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_completion_tokens=4096,
    )
    output = (response.choices[0].message.content or "").strip()
    translations = []

    for i in range(len(batch)):
        match = re.search(
            rf"<SEGMENT_{i:04d}>\s*(.*?)\s*</SEGMENT_{i:04d}>",
            output,
            re.DOTALL,
        )
        if not match:
            raise ValueError(f"Missing translation for segment {i}")
        translations.append(match.group(1).strip())

    return translations


def translate_segments(segments, src_lang="es", tgt_lang="en"):
    """Translate segments in GPT-OSS-20B batches."""
    if not segments:
        return []

    client = _get_client()
    translated = []

    for start in range(0, len(segments), BATCH_SIZE):
        batch = segments[start:start + BATCH_SIZE]
        results = _translate_batch(client, batch, src_lang, tgt_lang)
        translated.extend(
            {**segment, "translated": text}
            for segment, text in zip(batch, results)
        )

    return translated


def translate_text(text, src_lang="es", tgt_lang="en"):
    """Translate one piece of text using the batch API."""
    if not text or not text.strip():
        return ""
    return translate_segments(
        [{"text": text}], src_lang, tgt_lang
    )[0]["translated"]

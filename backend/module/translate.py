import os
import re
import time
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "config", ".env"))

MODEL = "openai/gpt-oss-20b"
# Increased base batch size, but dynamically managed below
BATCH_SIZE = 25

SYSTEM_PROMPT = """You are a professional translator for AI video dubbing.

Translate each dialogue segment from the source language into the target language.

Your goal is a natural, conversational spoken translation that preserves the original speaker's meaning, tone, intent, humor, and style.

STRICT RULES:

1. Preserve the exact meaning and intent of the original.
2. Do not add information that is not present in the source.
3. Do not remove meaningful information from the source.
4. Do not summarize, explain, or rewrite the content.
5. Translate naturally for spoken dialogue rather than word-for-word when a literal translation sounds unnatural.
6. Preserve jokes, comparisons, metaphors, sarcasm, and other expressions whenever possible.
7. Do not change an analogy or comparison into a different statement.
8. Preserve names, people, places, brands, games, products, and technical terms. Use their established target-language form only when one exists.
9. Preserve the speaker's perspective, tense, and intent.
10. Keep each translation reasonably close to the length of the original segment.
11. Keep very short segments short. Do not add filler words.
12. Do not unnecessarily expand sentences just to make them sound more natural.
13. Do not combine, split, reorder, or omit dialogue segments.
14. Do not add introductions, explanations, comments, or translator notes.
15. Return ONLY the translated text inside the required segment tags.

IMPORTANT FOR DUBBING:
The translated dialogue will be spoken by a TTS voice.
Prefer natural spoken language that a person would actually say aloud.
Do not make the translation unnecessarily formal, literary, or verbose.

Return output strictly formatted as:
<SEGMENT_XXXX>translated text</SEGMENT_XXXX>"""

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

def _translate_batch_with_retry(client, batch, src_lang, tgt_lang, max_retries=5):
    """Executes a batch translation with exponential backoff for rate limits."""
    from groq import RateLimitError

    # Build prompt payload using index relative to the current batch
    segments_payload = "\n\n".join(
        f"<SEGMENT_{i:04d}>{item.get('text', '').strip()}</SEGMENT_{i:04d}>"
        for i, item in enumerate(batch)
    )
    
    user_prompt = f"Source Language: {src_lang}\nTarget Language: {tgt_lang}\n\n{segments_payload}"

    delay = 2.0  # Initial wait time in seconds

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
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
                    raise ValueError(f"Missing tag <SEGMENT_{i:04d}> in LLM output")
                translations.append(match.group(1).strip())

            return translations

        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise e
            print(f"⚠️ Hit Groq 8k TPM Limit. Retrying in {delay:.1f}s... (Attempt {attempt + 1}/{max_retries})")
            time.sleep(delay)
            delay *= 2.0  # Exponential backoff

def translate_segments(segments, src_lang="es", tgt_lang="en"):
    """Translate segments in optimal batch sizes with rate-limit protection."""
    if not segments:
        return []

    client = _get_client()
    translated = []

    for start in range(0, len(segments), BATCH_SIZE):
        batch = segments[start : start + BATCH_SIZE]
        
        # Execute batch with automated backoff retry logic
        results = _translate_batch_with_retry(client, batch, src_lang, tgt_lang)
        
        translated.extend(
            {**segment, "translated": text}
            for segment, text in zip(batch, results)
        )
        
        # Small delay between batches to stay under the 8,000 TPM limit
        time.sleep(0.5)

    return translated

def translate_text(text, src_lang="es", tgt_lang="en"):
    """Translate one piece of text using the batch framework."""
    if not text or not text.strip():
        return ""
    return translate_segments([{"text": text}], src_lang, tgt_lang)[0]["translated"]

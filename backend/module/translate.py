import os
import re
import time
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "config", ".env"))

MODEL = "openai/gpt-oss-20b"
# Increased base batch size, but dynamically managed below
BATCH_SIZE = 25

SYSTEM_PROMPT = """You are a professional voice dubbing translator.
Translate the dialogue segments provided in the user message into natural spoken dialogue.
Preserve exact meaning, tone, character names, and segment order. 
Do not add explanations, notes, or intros.

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

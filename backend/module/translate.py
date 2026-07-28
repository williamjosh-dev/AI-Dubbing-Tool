import os
from dotenv import load_dotenv
from deep_translator import GoogleTranslator

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', 'config', '.env'))

def translate_text(text, src_lang="es", tgt_lang="en"):
    """
    Translate text using deep-translator.
    """

    if not text:
        return ""

    try:
        translator = GoogleTranslator(source=src_lang, target=tgt_lang)
        translation = translator.translate(text)

        print(f"🌍 Translated: {translation}")

        return translation.strip()

    except Exception as e:
        print(f"❌ Translation error: {e}")
        return text  # fallback (VERY IMPORTANT)
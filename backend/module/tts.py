import os
import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', 'config', '.env'))

# Global clients / configs
_elevenlabs_client = None
ZONOS2_ENDPOINT = os.getenv("ZONOS2_ENDPOINT", "http://localhost:1919/tts/generate")


def _get_elevenlabs_client():
    """
    Get or create ElevenLabs client (singleton pattern).
    """
    global _elevenlabs_client

    if _elevenlabs_client is None:
        try:
            print("🎙️ Initializing ElevenLabs TTS client...")
            from elevenlabs.client import ElevenLabs

            api_key = os.getenv('ELEVENLABS_API_KEY')
            if not api_key:
                raise ValueError("ELEVENLABS_API_KEY environment variable not set")

            _elevenlabs_client = ElevenLabs(api_key=api_key)
            print("✅ ElevenLabs TTS client initialized successfully")

        except ImportError:
            raise ImportError(
                "ElevenLabs SDK not installed. "
                "Run: pip install elevenlabs"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize ElevenLabs TTS: {e}") from e

    return _elevenlabs_client


def _generate_speech_elevenlabs(text, output_path):
    """
    Generate speech using ElevenLabs TTS.
    """
    try:
        print("🎵 Generating speech with ElevenLabs...")
        client = _get_elevenlabs_client()

        # Generate audio iterator
        audio_stream = client.generate(
            text=text,
            voice="Rachel",  # Default voice, can be adjusted
            model="eleven_multilingual_v2"
        )

        with open(output_path, "wb") as f:
            for chunk in audio_stream:
                f.write(chunk)

        print(f"✅ ElevenLabs speech generated: {output_path}")
        return output_path

    except Exception as e:
        print(f"❌ ElevenLabs TTS failed: {e}")
        raise


def _generate_speech_zonos2(text, output_path, language="en_us"):
    """
    Generate speech using Zonos 2 inference server/API.
    """
    try:
        print("🎵 Generating speech with Zonos 2...")

        payload = {
            "text": text,
            "language": language,
            "stream": False
        }

        response = requests.post(
            ZONOS2_ENDPOINT,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        response.raise_for_status()

        with open(output_path, "wb") as f:
            f.write(response.content)

        print(f"✅ Zonos 2 speech generated: {output_path}")
        return output_path

    except Exception as e:
        print(f"❌ Zonos 2 TTS failed: {e}")
        raise


def _generate_speech_gtts(text, output_path):
    """
    Generate speech using Google Text-to-Speech (gTTS) as fallback.
    """
    try:
        print("🎵 Generating speech with gTTS (fallback)...")
        from gtts import gTTS

        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(output_path)

        print(f"✅ gTTS speech generated: {output_path}")
        return output_path

    except Exception as e:
        print(f"❌ gTTS failed: {e}")
        raise


def generate_speech(text, output_path, voice_method="auto"):
    """
    Generate speech from text using multiple TTS services with automatic fallback.

    Args:
        text (str): Text to convert to speech
        output_path (str): Full path where to save the audio file
        voice_method (str): 'auto', 'zonos2', 'elevenlabs', or 'gtts'. Defaults to 'auto'.

    Returns:
        str: Path to the generated audio file
    """
    if not text or not text.strip():
        raise ValueError("No text provided for speech generation")

    if not output_path:
        raise ValueError("No output path provided")

    output_dir = os.path.dirname(output_path) or "."
    os.makedirs(output_dir, exist_ok=True)

    if not output_path.lower().endswith(('.wav', '.mp3')):
        output_path = output_path.rsplit('.', 1)[0] + '.mp3'

    print(f"🎵 Generating speech for text: '{text[:50]}...'")

    # Normalize method selection
    voice_method = (voice_method or "auto").lower()

    if voice_method in ('auto', 'zonos2'):
        # Auto mode & Zonos2 mode: Try Zonos 2 first -> ElevenLabs -> gTTS
        tts_methods = [
            ("Zonos 2", _generate_speech_zonos2),
            ("ElevenLabs", _generate_speech_elevenlabs),
            ("gTTS", _generate_speech_gtts),
        ]
    elif voice_method == 'elevenlabs':
        tts_methods = [
            ("ElevenLabs", _generate_speech_elevenlabs),
            ("Zonos 2", _generate_speech_zonos2),
            ("gTTS", _generate_speech_gtts),
        ]
    elif voice_method == 'gtts':
        tts_methods = [
            ("gTTS", _generate_speech_gtts),
        ]
    else:
        # Fallback to default auto behavior for unknown options
        tts_methods = [
            ("Zonos 2", _generate_speech_zonos2),
            ("ElevenLabs", _generate_speech_elevenlabs),
            ("gTTS", _generate_speech_gtts),
        ]

    last_error = None

    for method_name, tts_func in tts_methods:
        try:
            print(f"🔄 Trying {method_name}...")
            result_path = tts_func(text, output_path)

            if os.path.exists(result_path) and os.path.getsize(result_path) > 0:
                print(f"✅ Successfully generated speech using {method_name}")
                return result_path
            else:
                raise RuntimeError(f"{method_name} generated empty or missing file")

        except Exception as e:
            error_msg = f"{method_name} failed: {e}"
            print(f"❌ {error_msg}")
            last_error = e

            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except Exception:
                    pass

            continue

    raise RuntimeError(f"All TTS methods failed. Last error: {last_error}") from last_error

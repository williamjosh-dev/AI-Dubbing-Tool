import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', 'config', '.env'))

# Global clients
_tts_client = None
_elevenlabs_client = None
_coqui_tts = None


def _get_google_cloud_client():
    """
    Get or create Google Cloud TTS client (singleton pattern).
    Client is reused across multiple calls for efficiency.
    """
    global _tts_client

    if _tts_client is None:
        try:
            print("🎙️ Initializing Google Cloud TTS client...")
            from google.cloud import texttospeech

            _tts_client = texttospeech.TextToSpeechClient()
            print("✅ Google Cloud TTS client initialized successfully")

        except ImportError:
            raise ImportError(
                "Google Cloud TTS SDK not installed. "
                "Run: pip install google-cloud-texttospeech"
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to initialize Google Cloud TTS: {e}\n"
                "Ensure GOOGLE_APPLICATION_CREDENTIALS environment variable is set "
                "to point to your service account JSON file."
            ) from e

    return _tts_client


def _get_elevenlabs_client():
    """
    Get or create ElevenLabs client (singleton pattern).
    """
    global _elevenlabs_client

    if _elevenlabs_client is None:
        try:
            print("🎙️ Initializing ElevenLabs TTS client...")
            from elevenlabs import ElevenLabs

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


def _get_coqui_tts():
    """
    Get or create Coqui TTS model (singleton pattern).
    """
    global _coqui_tts

    if _coqui_tts is None:
        try:
            print("🎙️ Initializing Coqui TTS...")
            from TTS.api import TTS

            # Use a default model, can be configured
            _coqui_tts = TTS("tts_models/en/ljspeech/tacotron2-DDC").to("cpu")
            print("✅ Coqui TTS initialized successfully")

        except ImportError:
            raise ImportError(
                "Coqui TTS not installed. "
                "Run: pip install TTS"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Coqui TTS: {e}") from e

    return _coqui_tts


def _generate_speech_elevenlabs(text, output_path):
    """
    Generate speech using ElevenLabs TTS.
    """
    try:
        from elevenlabs import ElevenLabs

        print("🎵 Generating speech with ElevenLabs...")

        client = _get_elevenlabs_client()

        # Generate audio
        audio = client.generate(
            text=text,
            voice="Rachel",  # Default voice, can be configured
            model="eleven_monolingual_v1"
        )

        # Save to file
        with open(output_path, "wb") as f:
            f.write(audio)

        print(f"✅ ElevenLabs speech generated: {output_path}")
        return output_path

    except Exception as e:
        print(f"❌ ElevenLabs TTS failed: {e}")
        raise


def _generate_speech_coqui(text, output_path):
    """
    Generate speech using Coqui TTS.
    """
    try:
        print("🎵 Generating speech with Coqui TTS...")

        tts = _get_coqui_tts()

        # Generate audio
        tts.tts_to_file(text=text, file_path=output_path)

        print(f"✅ Coqui TTS speech generated: {output_path}")
        return output_path

    except Exception as e:
        print(f"❌ Coqui TTS failed: {e}")
        raise


def _generate_speech_gtts(text, output_path):
    """
    Generate speech using Google Text-to-Speech (gTTS) as fallback.
    """
    try:
        print("🎵 Generating speech with gTTS (fallback)...")

        from gtts import gTTS

        # Create gTTS object
        tts = gTTS(text=text, lang='en', slow=False)

        # Save to file
        tts.save(output_path)

        print(f"✅ gTTS speech generated: {output_path}")
        return output_path

    except Exception as e:
        print(f"❌ gTTS failed: {e}")
        raise
def _generate_speech_google_cloud(text, output_path):
    """
    Generate speech from text using Google Cloud Text-to-Speech.

    Args:
        text (str): Text to convert to speech
        output_path (str): Full path where to save the WAV file

    Returns:
        str: Path to the generated audio file

    Raises:
        RuntimeError: If speech generation fails
    """
    if not text or not text.strip():
        raise ValueError("No text provided for speech generation")

    if not output_path:
        raise ValueError("No output path provided")

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path) or "."
    os.makedirs(output_dir, exist_ok=True)

    # Ensure output has .wav or .mp3 extension (Google Cloud TTS supports multiple formats)
    if not output_path.lower().endswith(('.wav', '.mp3')):
        output_path = output_path.rsplit('.', 1)[0] + '.wav'

    try:
        from google.cloud import texttospeech

        print(f"🎵 Generating speech for text: '{text[:50]}...'")

        # Get or create client
        client = _get_google_cloud_client()

        # Set the text input to be synthesized
        synthesis_input = texttospeech.SynthesisInput(text=text)

        # Build the voice request: use a natural English voice
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Neural2-C",  # High-quality neural voice (female)
            # Alternative options:
            # "en-US-Neural2-A" (male), "en-US-Neural2-B" (male), "en-US-Neural2-E" (female)
        )

        # Select the type of audio file you want returned
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16,  # WAV format
            speaking_rate=1.0,  # Normal speed
            pitch=0.0,  # Normal pitch
        )

        # Perform the text-to-speech request
        print("🔄 Calling Google Cloud TTS API...")
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config,
        )

        # Write the response to the output file
        with open(output_path, "wb") as out:
            out.write(response.audio_content)

        # Verify file was created
        if not os.path.exists(output_path):
            raise RuntimeError("Audio file was not created")

        file_size = os.path.getsize(output_path)
        if file_size == 0:
            raise RuntimeError("Generated audio file is empty")

        print(f"✅ Speech generated successfully: {output_path} ({file_size} bytes)")
        return output_path

    except ImportError as e:
        raise ImportError(
            "Google Cloud TTS SDK not installed. "
            "Install with: pip install google-cloud-texttospeech"
        ) from e
    except Exception as e:
        error_msg = f"Speech generation failed: {e}"
        print(f"❌ {error_msg}")

        # Clean up partial file if it exists
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
                print(f"🧹 Cleaned up partial file: {output_path}")
            except Exception:
                pass

        raise RuntimeError(error_msg) from e


def generate_speech(text, output_path):
    """
    Generate speech from text using multiple TTS services with fallback to gTTS.

    Tries TTS services in order:
    1. ElevenLabs (voice cloning)
    2. Coqui TTS
    3. Google Cloud TTS
    4. gTTS (final fallback)

    Args:
        text (str): Text to convert to speech
        output_path (str): Full path where to save the audio file

    Returns:
        str: Path to the generated audio file

    Raises:
        ValueError: If text is empty or invalid
        RuntimeError: If all speech generation methods fail
    """
    if not text or not text.strip():
        raise ValueError("No text provided for speech generation")

    if not output_path:
        raise ValueError("No output path provided")

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path) or "."
    os.makedirs(output_dir, exist_ok=True)

    # Ensure output has .wav or .mp3 extension
    if not output_path.lower().endswith(('.wav', '.mp3')):
        output_path = output_path.rsplit('.', 1)[0] + '.wav'

    print(f"🎵 Generating speech for text: '{text[:50]}...'")

    # List of TTS functions to try in order
    tts_methods = [
        ("ElevenLabs", _generate_speech_elevenlabs),
        ("Coqui TTS", _generate_speech_coqui),
        ("Google Cloud TTS", _generate_speech_google_cloud),
        ("gTTS", _generate_speech_gtts),
    ]

    last_error = None

    for method_name, tts_func in tts_methods:
        try:
            print(f"🔄 Trying {method_name}...")
            result_path = tts_func(text, output_path)

            # Verify file was created and is not empty
            if os.path.exists(result_path) and os.path.getsize(result_path) > 0:
                print(f"✅ Successfully generated speech using {method_name}")
                return result_path
            else:
                raise RuntimeError(f"{method_name} generated empty or missing file")

        except Exception as e:
            error_msg = f"{method_name} failed: {e}"
            print(f"❌ {error_msg}")
            last_error = e

            # Clean up any partial file
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except Exception:
                    pass

            continue

    # If all methods failed
    raise RuntimeError(f"All TTS methods failed. Last error: {last_error}") from last_error
   
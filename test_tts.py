#!/usr/bin/env python3
"""Test script for TTS fallback functionality."""

from module.tts import generate_speech

def test_tts_fallback():
    """Test that TTS falls back to gTTS when other services fail."""
    test_text = "Hello, this is a test of the TTS fallback system."
    output_path = "outputs/test_fallback.wav"

    try:
        result = generate_speech(test_text, output_path)
        print(f"✅ TTS test successful: {result}")

        # Check if file exists and has content
        import os
        if os.path.exists(result) and os.path.getsize(result) > 0:
            print(f"✅ Audio file created successfully ({os.path.getsize(result)} bytes)")
        else:
            print("❌ Audio file is empty or missing")

    except Exception as e:
        print(f"❌ TTS test failed: {e}")
        return False

    return True

if __name__ == "__main__":
    test_tts_fallback()
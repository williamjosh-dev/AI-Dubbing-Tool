"""High-level audio translation pipeline.

This pipeline orchestrates the existing modules in `module/`:
- `module/transcribe.py` for audio transcription
- `module/translate.py` for text translation
- `module/tts.py` for speech synthesis

The pipeline provides a clear end-to-end flow from audio input to translated speech output.
"""

import argparse
import os
from pathlib import Path
from typing import List

from module.transcribe import transcribe_audio
from module.translate import translate_text
from module.tts import generate_speech


class AudioTranslationPipeline:
    """High-level pipeline to transcribe, translate, and synthesize audio."""

    def __init__(self, src_lang: str = "es", tgt_lang: str = "en", voice_method: str | None = None):
        self.src_lang = src_lang
        self.tgt_lang = tgt_lang
        self.voice_method = voice_method

    def transcribe(self, audio_path: str) -> List[dict]:
        """Transcribe audio into timestamped text segments."""
        return transcribe_audio(audio_path)

    def translate(self, text: str) -> str:
        """Translate text from source language to target language."""
        return translate_text(text, src_lang=self.src_lang, tgt_lang=self.tgt_lang)

    def synthesize(self, text: str, output_path: str) -> str:
        """Synthesize translated text into an audio file."""
        return generate_speech(text, output_path, voice_method=self.voice_method)

    def run(
        self,
        audio_path: str,
        output_audio_path: str,
        transcript_path: str | None = None,
        save_translated_text: bool = False,
    ) -> dict:
        """Execute the full pipeline and return metadata."""
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Input audio not found: {audio_path}")

        segments = self.transcribe(audio_path)
        if not segments:
            raise RuntimeError("Transcription returned no segments.")

        full_text = " ".join(segment["text"] for segment in segments)
        translated_text = self.translate(full_text)

        output_audio_path = self.synthesize(translated_text, output_audio_path)

        if transcript_path:
            self._save_transcript(transcript_path, segments, translated_text)

        if save_translated_text and transcript_path is None:
            translated_text_path = Path(output_audio_path).with_suffix(".txt")
            self._write_file(translated_text_path, translated_text)

        return {
            "input_audio": audio_path,
            "output_audio": output_audio_path,
            "translated_text": translated_text,
            "segments": segments,
        }

    def _save_transcript(self, transcript_path: str, segments: List[dict], translated_text: str) -> None:
        """Save both original transcript segments and translated text."""
        transcript_dir = Path(transcript_path).parent
        transcript_dir.mkdir(parents=True, exist_ok=True)

        with open(transcript_path, "w", encoding="utf-8") as f:
            f.write("Original segments:\n")
            for segment in segments:
                f.write(f"[{segment['start']:.2f} - {segment['end']:.2f}] {segment['text']}\n")
            f.write("\nTranslated text:\n")
            f.write(translated_text)

    @staticmethod
    def _write_file(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the audio translation pipeline.")
    parser.add_argument("input_audio", help="Path to the source audio file")
    parser.add_argument(
        "output_audio",
        help="Path to save the synthesized translated audio file",
    )
    parser.add_argument(
        "--src-lang",
        default="es",
        help="Source language code for transcription and translation (default: es)",
    )
    parser.add_argument(
        "--tgt-lang",
        default="en",
        help="Target language code for translation (default: en)",
    )
    parser.add_argument(
        "--transcript",
        help="Optional path to save a combined transcript and translation text file",
    )
    parser.add_argument(
        "--save-text",
        action="store_true",
        help="Save translated text to a .txt file next to the output audio",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pipeline = AudioTranslationPipeline(src_lang=args.src_lang, tgt_lang=args.tgt_lang)

    result = pipeline.run(
        audio_path=args.input_audio,
        output_audio_path=args.output_audio,
        transcript_path=args.transcript,
        save_translated_text=args.save_text,
    )

    print("\n✅ Pipeline completed successfully")
    print(f"Input audio: {result['input_audio']}")
    print(f"Output audio: {result['output_audio']}")
    print(f"Translated text length: {len(result['translated_text'])} characters")


if __name__ == "__main__":
    main()

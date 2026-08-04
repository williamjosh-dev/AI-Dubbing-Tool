"""
High-level audio translation pipeline.

This pipeline orchestrates the existing modules in `module/`:
- `module/transcribe.py` for audio transcription
- `module/translate.py` for text translation
- `module/tts.py` for speech synthesis
"""

import argparse
import os
import tempfile
from pathlib import Path
from typing import List

from pydub import AudioSegment

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
        return transcribe_audio(audio_path, language=self.src_lang)

    def translate(self, text: str) -> str:
        """Translate text from source language to target language."""
        return translate_text(text, src_lang=self.src_lang, tgt_lang=self.tgt_lang)

    def synthesize(self, text: str, output_path: str, reference_audio: str | None = None) -> str:
        """Synthesize translated text into an audio file."""
        # Note: If your module/tts.py supports reference_audio for voice cloning, 
        # you can pass reference_audio here.
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

        # 1. Translate each segment individually
        translated_segments = []
        for segment in segments:
            seg_text = segment.get("text", "")
            translated = self.translate(seg_text) if seg_text else ""
            translated_segments.append({
                "start": segment.get("start", 0.0),
                "end": segment.get("end", 0.0),
                "text": seg_text,
                "translated": translated,
            })

        # 2. Segment-by-segment synthesis & timeline reconstruction
        print("🎙️ Synthesizing segment-by-segment for sync...")
        timeline_audio = AudioSegment.silent(duration=0)
        current_position_ms = 0

        with tempfile.TemporaryDirectory() as temp_dir:
            for i, seg in enumerate(translated_segments):
                translated_text = seg.get("translated", "").strip()
                if not translated_text:
                    continue

                start_ms = int(seg["start"] * 1000)
                end_ms = int(seg["end"] * 1000)
                target_duration_ms = end_ms - start_ms

                # Add silence gap before this segment if needed
                if start_ms > current_position_ms:
                    silence_padding = start_ms - current_position_ms
                    timeline_audio += AudioSegment.silent(duration=silence_padding)
                    current_position_ms = start_ms

                # Synthesize individual segment
                seg_file = os.path.join(temp_dir, f"seg_{i}.wav")
                self.synthesize(translated_text, seg_file, reference_audio=audio_path)

                if os.path.exists(seg_file):
                    seg_audio = AudioSegment.from_file(seg_file)
                    
                    # Optional: speed adjust if segment audio is significantly longer than original slot
                    # If audio length > target_duration, you can apply time-stretching here if needed.
                    
                    timeline_audio += seg_audio
                    current_position_ms += len(seg_audio)

            # Export the assembled timeline audio
            out_format = Path(output_audio_path).suffix.lstrip(".").lower() or "wav"
            timeline_audio.export(output_audio_path, format=out_format)

        full_translated_text = " ".join(s["translated"] for s in translated_segments if s.get("translated"))

        if transcript_path:
            self._save_transcript(transcript_path, segments, translated_segments)

        if save_translated_text and transcript_path is None:
            translated_text_path = Path(output_audio_path).with_suffix(".txt")
            self._write_file(translated_text_path, full_translated_text)

        return {
            "input_audio": audio_path,
            "output_audio": output_audio_path,
            "translated_text": full_translated_text,
            "translated_segments": translated_segments,
            "segments": segments,
        }

    def _save_transcript(self, transcript_path: str, segments: List[dict], translated_segments: List[dict]) -> None:
        """Save both original transcript segments and per-segment translated text."""
        transcript_dir = Path(transcript_path).parent
        transcript_dir.mkdir(parents=True, exist_ok=True)

        with open(transcript_path, "w", encoding="utf-8") as f:
            f.write("Original segments:\n")
            for segment in segments:
                f.write(f"[{segment['start']:.2f} - {segment['end']:.2f}] {segment['text']}\n")

            f.write("\nTranslated segments:\n")
            for tseg in translated_segments:
                f.write(f"[{tseg['start']:.2f} - {tseg['end']:.2f}] {tseg.get('translated','')}\n")

    @staticmethod
    def _write_file(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the audio translation pipeline.")
    parser.add_argument("input_audio", help="Path to the source audio file")
    parser.add_argument("output_audio", help="Path to save synthesized audio file")
    parser.add_argument("--src-lang", default="es", help="Source language code")
    parser.add_argument("--tgt-lang", default="en", help="Target language code")
    parser.add_argument("--transcript", help="Optional path to save transcript file")
    parser.add_argument("--save-text", action="store_true", help="Save translated text file")
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

    print("\n✅ Segmented Pipeline completed successfully")
    print(f"Input audio: {result['input_audio']}")
    print(f"Output audio: {result['output_audio']}")


if __name__ == "__main__":
    main()
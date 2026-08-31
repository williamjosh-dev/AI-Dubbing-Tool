import os
import tempfile
import torch
import torchaudio
from demucs.apply import apply_model
from demucs.audio import AudioFile
from demucs.pretrained import get_model


class DemucsBackend:
    def __init__(self, model_name: str = "htdemucs", device: str = "cuda"):
        self.device = device if torch.cuda.is_available() else "cpu"
        self.model = get_model(model_name)
        self.model.to(self.device)
        self.model.eval()

    def separate_stems(
        self, audio_bytes: bytes, stems: list[str] = ["vocals", "no_vocals"]
    ) -> dict[str, bytes]:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_in:
            tmp_in.write(audio_bytes)
            tmp_in_path = tmp_in.name

        try:
            wav = AudioFile(tmp_in_path).read(
                streams=0,
                samplerate=self.model.samplerate,
                channels=self.model.audio_channels,
            )
            ref = wav.mean(0)
            wav = (wav - ref.mean()) / ref.std()
            wav = wav.to(self.device)

            with torch.no_grad():
                sources = apply_model(
                    self.model,
                    wav[None],
                    device=self.device,
                    shifts=1,
                    split=True,
                    overlap=0.25,
                )[0]

            sources = sources * ref.std() + ref.mean()
            source_names = self.model.sources
            result_stems = {}

            for stem_name in stems:
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_out:
                    tmp_out_path = tmp_out.name

                if stem_name == "vocals":
                    vocal_idx = source_names.index("vocals")
                    torchaudio.save(
                        tmp_out_path, sources[vocal_idx].cpu(), self.model.samplerate
                    )
                elif stem_name in ["no_vocals", "instrumental"]:
                    vocal_idx = source_names.index("vocals")
                    bg_indices = [i for i in range(len(source_names)) if i != vocal_idx]
                    bg_tensor = sources[bg_indices].sum(dim=0).cpu()
                    torchaudio.save(tmp_out_path, bg_tensor, self.model.samplerate)

                with open(tmp_out_path, "rb") as f:
                    result_stems[stem_name] = f.read()

                os.remove(tmp_out_path)

            return result_stems
        finally:
            if os.path.exists(tmp_in_path):
                os.remove(tmp_in_path)
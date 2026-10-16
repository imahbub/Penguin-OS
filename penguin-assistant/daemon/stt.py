"""Speech-to-Text (STT) inference using whisper.cpp or Faster-Whisper."""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional
from .config import Config


class STTEngine:
    """Performs speech transcription from audio wav files or PCM buffers."""

    def __init__(self, config: Config):
        self.config = config
        self.model_path = self.config.get_model_path(self.config.get("models", "whisper_model"))

    def transcribe_wav(self, wav_path: str) -> Optional[str]:
        """Transcribe audio from a WAV file."""
        if not os.path.isfile(wav_path):
            return None

        # 1. Native whisper-cli / whisper.cpp binary
        for bin_name in ["whisper-cli", "whisper-cpp", "whisper"]:
            whisper_bin = shutil.which(bin_name)
            if whisper_bin and self.model_path.is_file():
                try:
                    cmd = [
                        whisper_bin,
                        "-m", str(self.model_path),
                        "-f", wav_path,
                        "--no-timestamps",
                        "-nt"
                    ]
                    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=10)
                    if res.returncode == 0:
                        text = res.stdout.strip()
                        # Clean whisper bracket annotations like [BLANK_AUDIO] or (music)
                        text = " ".join([w for w in text.split() if not (w.startswith("[") and w.endswith("]"))])
                        return text
                except Exception:
                    pass

        # 2. Python faster-whisper fallback if installed
        try:
            from faster_whisper import WhisperModel
            model = WhisperModel("base.en", device="cpu", compute_type="int8")
            segments, _ = model.transcribe(wav_path, beam_size=1)
            transcription = " ".join([seg.text for seg in segments]).strip()
            return transcription
        except Exception:
            pass

        return None

"""Text-to-Speech (TTS) synthesis using Piper TTS with PipeWire streaming."""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional
from .config import Config


class TTSEngine:
    """Synthesizes text to spoken audio using Piper TTS or system fallbacks."""

    def __init__(self, config: Config):
        self.config = config
        self.model_path = self.config.get_model_path(self.config.get("models", "piper_model"))
        self.config_path = self.config.get_model_path(self.config.get("models", "piper_config"))

    def speak(self, text: str) -> bool:
        """Synthesize text and play it immediately via PipeWire."""
        if not text.strip():
            return True

        # 1. Try Piper TTS if binary and model exist
        piper_bin = shutil.which("piper")
        if piper_bin and self.model_path.is_file():
            try:
                cmd = [
                    piper_bin,
                    "--model", str(self.model_path),
                    "--output_raw"
                ]
                if self.config_path.is_file():
                    cmd.extend(["--config", str(self.config_path)])

                # Piper outputs 22050Hz 16-bit mono PCM by default
                piper_proc = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL
                )

                # Pipe directly to pw-play
                pw_bin = shutil.which("pw-play") or shutil.which("paplay")
                if pw_bin:
                    pw_cmd = [
                        pw_bin,
                        "--rate", "22050",
                        "--channels", "1",
                        "--format", "s16",
                        "-"
                    ]
                    pw_proc = subprocess.Popen(
                        pw_cmd,
                        stdin=piper_proc.stdout,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    piper_proc.stdin.write(text.encode("utf-8"))
                    piper_proc.stdin.close()
                    pw_proc.wait(timeout=10)
                    return True
            except Exception:
                pass

        # 2. Fallback to spd-say (standard Linux speech-dispatcher)
        if shutil.which("spd-say"):
            subprocess.run(["spd-say", "-r", "10", text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True

        # 3. Fallback to espeak-ng
        if shutil.which("espeak-ng"):
            subprocess.run(["espeak-ng", text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True

        return False

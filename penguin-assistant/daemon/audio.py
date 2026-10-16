"""Audio input/output management using PipeWire (pw-record/pw-play)."""

import io
import os
import shutil
import subprocess
import wave
from typing import Optional, Generator


class AudioManager:
    """Manages audio capture and playback via PipeWire."""

    def __init__(self, sample_rate: int = 16000, channels: int = 1):
        self.sample_rate = sample_rate
        self.channels = channels
        self._record_proc: Optional[subprocess.Popen] = None

    def start_recording_stream(self) -> Optional[subprocess.Popen]:
        """Start capturing raw 16-bit PCM audio from the default PipeWire source."""
        if shutil.which("pw-record"):
            cmd = [
                "pw-record",
                "--rate", str(self.sample_rate),
                "--channels", str(self.channels),
                "--format", "s16",
                "-"
            ]
        elif shutil.which("parec"):
            cmd = [
                "parec",
                f"--rate={self.sample_rate}",
                f"--channels={self.channels}",
                "--format=s16le"
            ]
        elif shutil.which("arecord"):
            cmd = [
                "arecord",
                "-r", str(self.sample_rate),
                "-c", str(self.channels),
                "-f", "S16_LE",
                "-t", "raw"
            ]
        else:
            return None

        self._record_proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=4096
        )
        return self._record_proc

    def stop_recording(self):
        """Stop active audio recording process."""
        if self._record_proc:
            try:
                self._record_proc.terminate()
                self._record_proc.wait(timeout=1.0)
            except Exception:
                self._record_proc.kill()
            self._record_proc = None

    @staticmethod
    def pcm_to_wav_bytes(pcm_data: bytes, sample_rate: int = 16000, channels: int = 1) -> bytes:
        """Encapsulate raw PCM frames in a valid WAV container."""
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(sample_rate)
            wf.writeframes(pcm_data)
        return buffer.getvalue()

    def play_wav_file(self, wav_path: str) -> bool:
        """Play a WAV audio file via PipeWire."""
        if shutil.which("pw-play"):
            cmd = ["pw-play", wav_path]
        elif shutil.which("paplay"):
            cmd = ["paplay", wav_path]
        elif shutil.which("aplay"):
            cmd = ["aplay", wav_path]
        else:
            return False

        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return res.returncode == 0

    def play_pcm_stream(self, pcm_data: bytes, sample_rate: int = 22050, channels: int = 1) -> bool:
        """Play raw PCM data via PipeWire."""
        if shutil.which("pw-play"):
            cmd = [
                "pw-play",
                "--rate", str(sample_rate),
                "--channels", str(channels),
                "--format", "s16",
                "-"
            ]
        elif shutil.which("paplay"):
            cmd = [
                "paplay",
                f"--rate={sample_rate}",
                f"--channels={channels}",
                "--format=s16le",
                "--raw"
            ]
        elif shutil.which("aplay"):
            cmd = [
                "aplay",
                "-r", str(sample_rate),
                "-c", str(channels),
                "-f", "S16_LE",
                "-t", "raw"
            ]
        else:
            return False

        try:
            p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            p.communicate(input=pcm_data)
            return p.returncode == 0
        except Exception:
            return False

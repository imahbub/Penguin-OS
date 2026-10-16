"""Wake word detection using OpenWakeWord (ONNX Runtime)."""

import os
from pathlib import Path
from typing import Optional
from .config import Config


class WakeWordDetector:
    """Monitors live audio stream for the wake phrase (e.g. 'Hey Penguin')."""

    def __init__(self, config: Config):
        self.config = config
        self.enabled = self.config.getboolean("assistant", "wake_word_enabled")
        self.model_path = self.config.get_model_path(self.config.get("models", "openwakeword_model"))
        self._oww_model = None

        if self.enabled:
            self._init_engine()

    def _init_engine(self):
        try:
            import openwakeword
            from openwakeword.model import Model

            if self.model_path.is_file():
                self._oww_model = Model(wakeword_models=[str(self.model_path)], inference_framework="onnx")
            else:
                # Load default model if custom hey_penguin model is not yet compiled
                self._oww_model = Model(inference_framework="onnx")
        except Exception:
            self._oww_model = None

    def process_frame(self, frame_pcm: bytes) -> bool:
        """
        Process a 16kHz 16-bit PCM frame (recommended 1280 samples / 80ms).
        Returns True if wake word is detected.
        """
        if not self.enabled or self._oww_model is None:
            return False

        try:
            import numpy as np
            audio_data = np.frombuffer(frame_pcm, dtype=np.int16)
            prediction = self._oww_model.predict(audio_data)
            for model_name, score in self._oww_model.prediction_buffer.items():
                if score[-1] > 0.5:
                    self._oww_model.reset()
                    return True
        except Exception:
            pass

        return False

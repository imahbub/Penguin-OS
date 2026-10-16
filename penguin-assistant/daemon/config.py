"""Configuration manager for PenguinOS Voice Assistant."""

import os
from pathlib import Path
import configparser

DEFAULT_CONFIG = {
    "assistant": {
        "wake_word": "hey penguin",
        "wake_word_enabled": "true",
        "listen_timeout_seconds": "7.0",
        "silence_threshold_ms": "600",
        "sample_rate": "16000",
        "channels": "1",
    },
    "models": {
        "models_dir": "/usr/share/penguin-assistant/models",
        "user_models_dir": "~/.local/share/penguin-assistant/models",
        "whisper_model": "ggml-base.en-q8_0.bin",
        "piper_model": "en_US-lessac-medium.onnx",
        "piper_config": "en_US-lessac-medium.onnx.json",
        "openwakeword_model": "hey_penguin.onnx",
    },
    "speech": {
        "tts_engine": "piper",
        "speech_rate": "1.0",
        "feedback_sounds": "true",
    },
    "ui": {
        "show_overlay": "true",
        "overlay_timeout_seconds": "3.5",
        "theme": "dark",
    },
}


class Config:
    def __init__(self):
        self.config = configparser.ConfigParser()
        # Load defaults
        self.config.read_dict(DEFAULT_CONFIG)

        # Search paths for configuration
        candidate_paths = [
            Path("/etc/penguin-assistant/assistant.conf"),
            Path(__file__).parent.parent / "config" / "assistant.conf",
            Path(os.path.expanduser("~/.config/penguin-assistant/assistant.conf")),
        ]

        for p in candidate_paths:
            if p.is_file():
                self.config.read(str(p))

    def get(self, section: str, key: str, fallback=None) -> str:
        return self.config.get(section, key, fallback=fallback)

    def getint(self, section: str, key: str, fallback=0) -> int:
        return self.config.getint(section, key, fallback=fallback)

    def getfloat(self, section: str, key: str, fallback=0.0) -> float:
        return self.config.getfloat(section, key, fallback=fallback)

    def getboolean(self, section: str, key: str, fallback=False) -> bool:
        return self.config.getboolean(section, key, fallback=fallback)

    def get_model_path(self, model_name: str) -> Path:
        """Resolve model path looking first in user cache, then system path."""
        user_dir = Path(os.path.expanduser(self.get("models", "user_models_dir")))
        system_dir = Path(self.get("models", "models_dir"))

        user_target = user_dir / model_name
        if user_target.is_file():
            return user_target

        system_target = system_dir / model_name
        if system_target.is_file():
            return system_target

        # Fallback to local repo / development models dir if present
        dev_target = Path(__file__).parent.parent / "models" / model_name
        if dev_target.is_file():
            return dev_target

        return system_target

"""Voice Activity Detection (VAD) for streaming PCM audio."""

import math
import struct


class EnergyVAD:
    """Computes RMS energy and tracks speech vs silence states."""

    def __init__(self, sample_rate: int = 16000, silence_threshold_ms: int = 600, energy_threshold: float = 350.0):
        self.sample_rate = sample_rate
        self.silence_threshold_ms = silence_threshold_ms
        self.energy_threshold = energy_threshold
        self.silence_duration_ms = 0.0
        self.speech_detected = False

    def reset(self):
        self.silence_duration_ms = 0.0
        self.speech_detected = False

    @staticmethod
    def calculate_rms(chunk: bytes) -> float:
        """Calculate Root Mean Square (RMS) energy for 16-bit signed PCM."""
        if len(chunk) < 2:
            return 0.0
        count = len(chunk) // 2
        shorts = struct.unpack(f"{count}h", chunk[: count * 2])
        sum_squares = sum(s * s for s in shorts)
        return math.sqrt(sum_squares / count)

    def process_chunk(self, chunk: bytes, chunk_duration_ms: float) -> tuple[bool, bool]:
        """
        Process an audio chunk.
        Returns (is_speech_currently, is_speech_finished).
        """
        rms = self.calculate_rms(chunk)
        is_speech = rms >= self.energy_threshold

        if is_speech:
            self.speech_detected = True
            self.silence_duration_ms = 0.0
        elif self.speech_detected:
            self.silence_duration_ms += chunk_duration_ms
            if self.silence_duration_ms >= self.silence_threshold_ms:
                # Finished speaking
                return (False, True)

        return (is_speech, False)

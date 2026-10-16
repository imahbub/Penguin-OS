"""Core Orchestration Daemon for PenguinOS Voice Assistant."""

import asyncio
import os
import tempfile
import time
from typing import Dict, Any, Optional

from .config import Config
from .audio import AudioManager
from .vad import EnergyVAD
from .wakeword import WakeWordDetector
from .stt import STTEngine
from .dispatcher import ActionDispatcher
from .router import IntentRouter
from .tts import TTSEngine
from .ipc import IPCServer


class AssistantDaemon:
    """Central daemon managing voice pipeline states and IPC communication."""

    def __init__(self):
        self.config = Config()
        self.audio = AudioManager(
            sample_rate=self.config.getint("assistant", "sample_rate", 16000),
            channels=self.config.getint("assistant", "channels", 1)
        )
        self.vad = EnergyVAD(
            sample_rate=self.config.getint("assistant", "sample_rate", 16000),
            silence_threshold_ms=self.config.getint("assistant", "silence_threshold_ms", 600)
        )
        self.wakeword = WakeWordDetector(self.config)
        self.stt = STTEngine(self.config)
        self.dispatcher = ActionDispatcher()
        self.router = IntentRouter(self.dispatcher)
        self.tts = TTSEngine(self.config)
        self.ipc = IPCServer(self.handle_ipc_command)

        self.state = "idle"  # idle, listening, processing, executing, speaking
        self._manual_trigger_requested = False
        self._running = False

    def handle_ipc_command(self, cmd_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming command from CLI or UI client."""
        cmd = cmd_data.get("cmd")

        if cmd == "trigger":
            self._manual_trigger_requested = True
            return {"status": "ok", "message": "Listening triggered"}

        elif cmd == "exec":
            text = cmd_data.get("text", "")
            res = self.router.route_and_execute(text)
            self.ipc.broadcast({"event": "response", "text": res.get("response", ""), "domain": res.get("domain", "")})
            if cmd_data.get("speak", True):
                self.tts.speak(res.get("response", ""))
            return {"status": "ok", "result": res}

        elif cmd == "speak":
            text = cmd_data.get("text", "")
            self.tts.speak(text)
            return {"status": "ok", "message": "Spoken"}

        elif cmd == "status":
            return {
                "status": "ok",
                "state": self.state,
                "wake_word_enabled": self.wakeword.enabled
            }

        return {"status": "error", "message": f"Unknown command: {cmd}"}

    def _set_state(self, new_state: str):
        self.state = new_state
        self.ipc.broadcast({"event": "state_changed", "state": new_state})

    async def run(self):
        """Main service loop."""
        self._running = True
        await self.ipc.start()

        # Frame parameters (80ms chunk = 1280 samples at 16kHz = 2560 bytes)
        chunk_samples = 1280
        chunk_bytes = chunk_samples * 2
        chunk_duration_ms = 80.0
        listen_timeout = self.config.getfloat("assistant", "listen_timeout_seconds", 7.0)

        record_proc = self.audio.start_recording_stream()

        async def read_chunk() -> bytes:
            if not record_proc or not record_proc.stdout:
                await asyncio.sleep(0.05)
                return b""
            try:
                return await asyncio.to_thread(record_proc.stdout.read, chunk_bytes)
            except Exception:
                return b""

        try:
            while self._running:
                # 1. IDLE State: Wait for wake word or manual trigger
                self._set_state("idle")

                while self._running:
                    # Check manual trigger from IPC / hotkey
                    if self._manual_trigger_requested:
                        self._manual_trigger_requested = False
                        break

                    chunk = await read_chunk()
                    if not chunk:
                        await asyncio.sleep(0.05)
                        continue

                    if self.wakeword.process_frame(chunk):
                        break

                if not self._running:
                    break

                # 2. LISTENING State: Ingest user speech until silence or timeout
                self._set_state("listening")
                self.vad.reset()

                captured_pcm = bytearray()
                start_time = time.time()

                while self._running and (time.time() - start_time) < listen_timeout:
                    chunk = await read_chunk()
                    if not chunk:
                        await asyncio.sleep(0.02)
                        continue

                    captured_pcm.extend(chunk)
                    _, finished = self.vad.process_chunk(chunk, chunk_duration_ms)
                    if finished and len(captured_pcm) > chunk_bytes * 5:
                        # Finished speaking with at least 400ms audio
                        break

                if len(captured_pcm) < chunk_bytes * 3:
                    # No speech captured, return to idle
                    continue

                # 3. PROCESSING State: Transcribe audio to text
                self._set_state("processing")
                wav_bytes = self.audio.pcm_to_wav_bytes(
                    bytes(captured_pcm),
                    sample_rate=self.audio.sample_rate,
                    channels=self.audio.channels
                )

                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
                    tf.write(wav_bytes)
                    wav_path = tf.name

                try:
                    transcript = self.stt.transcribe_wav(wav_path)
                finally:
                    if os.path.exists(wav_path):
                        os.unlink(wav_path)

                if not transcript or not transcript.strip():
                    self.ipc.broadcast({"event": "response", "text": "I didn't catch that.", "domain": "none"})
                    continue

                self.ipc.broadcast({"event": "transcript", "text": transcript})

                # 4. EXECUTING State: Intent routing and system action dispatch
                self._set_state("executing")
                result = self.router.route_and_execute(transcript)
                response_text = result.get("response", "")

                self.ipc.broadcast({
                    "event": "response",
                    "text": response_text,
                    "domain": result.get("domain", "")
                })

                # 5. SPEAKING State: Piper TTS feedback
                self._set_state("speaking")
                self.tts.speak(response_text)

        finally:
            self.audio.stop_recording()
            await self.ipc.stop()


def main():
    daemon = AssistantDaemon()
    try:
        asyncio.run(daemon.run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

"""Deterministic Action Dispatcher for PenguinOS Voice Assistant.

Executes local actions via WirePlumber, MPRIS, brightnessctl, logind,
and desktop application loaders without requiring root permissions.
"""

import os
import shutil
import subprocess
from datetime import datetime
from typing import Dict, Any, Tuple


class ActionDispatcher:
    """Dispatches recognized intent commands to system IPC/services."""

    @staticmethod
    def _run_cmd(cmd: list[str]) -> Tuple[bool, str]:
        """Execute system command safely."""
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
            return (res.returncode == 0, res.stdout.strip())
        except Exception as e:
            return (False, str(e))

    # --- 1. Audio Control (WirePlumber / wpctl) ---

    def set_volume(self, percent: int) -> Tuple[bool, str]:
        percent = max(0, min(150, percent))
        # wpctl takes decimal (e.g. 0.50) or percent (e.g. 50%)
        ok, out = self._run_cmd(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"{percent}%"])
        if ok:
            return (True, f"Volume set to {percent} percent.")
        return (False, "Failed to adjust volume.")

    def change_volume(self, delta: int) -> Tuple[bool, str]:
        arg = f"{abs(delta)}%+" if delta > 0 else f"{abs(delta)}%-"
        ok, out = self._run_cmd(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", arg])
        if ok:
            direction = "increased" if delta > 0 else "decreased"
            return (True, f"Volume {direction}.")
        return (False, "Failed to adjust volume.")

    def set_mute(self, state: str = "toggle") -> Tuple[bool, str]:
        val = "toggle"
        if state == "mute":
            val = "1"
        elif state == "unmute":
            val = "0"
        ok, out = self._run_cmd(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", val])
        if ok:
            msg = "Muted." if state == "mute" else ("Unmuted." if state == "unmute" else "Audio mute toggled.")
            return (True, msg)
        return (False, "Failed to toggle audio mute.")

    # --- 2. Display Brightness (brightnessctl) ---

    def set_brightness(self, percent: int) -> Tuple[bool, str]:
        percent = max(5, min(100, percent))
        if shutil.which("brightnessctl"):
            ok, _ = self._run_cmd(["brightnessctl", "set", f"{percent}%"])
            if ok:
                return (True, f"Brightness set to {percent} percent.")
        return (False, "Brightness control is not available on this display.")

    def change_brightness(self, delta: int) -> Tuple[bool, str]:
        arg = f"+{abs(delta)}%" if delta > 0 else f"{abs(delta)}%-"
        if shutil.which("brightnessctl"):
            ok, _ = self._run_cmd(["brightnessctl", "set", arg])
            if ok:
                direction = "increased" if delta > 0 else "decreased"
                return (True, f"Brightness {direction}.")
        return (False, "Brightness control is not available.")

    # --- 3. Media Playback (MPRIS / playerctl) ---

    def media_play_pause(self) -> Tuple[bool, str]:
        if shutil.which("playerctl"):
            ok, _ = self._run_cmd(["playerctl", "play-pause"])
            if ok:
                return (True, "Playback toggled.")
        return (False, "No active media player found.")

    def media_play(self) -> Tuple[bool, str]:
        if shutil.which("playerctl"):
            ok, _ = self._run_cmd(["playerctl", "play"])
            if ok:
                return (True, "Playing.")
        return (False, "No active media player found.")

    def media_pause(self) -> Tuple[bool, str]:
        if shutil.which("playerctl"):
            ok, _ = self._run_cmd(["playerctl", "pause"])
            if ok:
                return (True, "Paused.")
        return (False, "No active media player found.")

    def media_next(self) -> Tuple[bool, str]:
        if shutil.which("playerctl"):
            ok, _ = self._run_cmd(["playerctl", "next"])
            if ok:
                return (True, "Playing next track.")
        return (False, "Cannot skip track.")

    def media_previous(self) -> Tuple[bool, str]:
        if shutil.which("playerctl"):
            ok, _ = self._run_cmd(["playerctl", "previous"])
            if ok:
                return (True, "Playing previous track.")
        return (False, "Cannot go to previous track.")

    # --- 4. System Power & Session (systemd / logind) ---

    def lock_screen(self) -> Tuple[bool, str]:
        ok, _ = self._run_cmd(["loginctl", "lock-session"])
        if ok:
            return (True, "Screen locked.")
        return (False, "Failed to lock screen.")

    def suspend(self) -> Tuple[bool, str]:
        self._run_cmd(["systemctl", "suspend"])
        return (True, "Suspending system.")

    def reboot(self) -> Tuple[bool, str]:
        self._run_cmd(["systemctl", "reboot"])
        return (True, "Rebooting system.")

    def poweroff(self) -> Tuple[bool, str]:
        self._run_cmd(["systemctl", "poweroff"])
        return (True, "Shutting down system.")

    # --- 5. Application Launching ---

    def launch_app(self, app_name: str) -> Tuple[bool, str]:
        app_name_lower = app_name.lower().strip()
        app_map = {
            "craft launcher": ["craft-launcher"],
            "craft": ["craft-launcher"],
            "artcraft": ["craft-launcher"],
            "steam": ["steam"],
            "telegram": ["telegram-desktop"],
            "browser": ["xdg-open", "https://duckduckgo.com"],
            "firefox": ["firefox"],
            "terminal": ["konsole"],
            "konsole": ["konsole"],
            "files": ["dolphin"],
            "file manager": ["dolphin"],
            "dolphin": ["dolphin"],
            "settings": ["systemsettings"],
            "system settings": ["systemsettings"],
            "calculator": ["kcalc"],
            "stremio": ["stremio"],
            "figma": ["xdg-open", "https://www.figma.com"],
            "waydroid": ["waydroid", "show-full-ui"],
        }

        cmd = app_map.get(app_name_lower)
        if not cmd:
            # Fallback to gtk-launch
            cmd = ["gtk-launch", app_name_lower]

        try:
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
            return (True, f"Opening {app_name}.")
        except Exception:
            return (False, f"Could not launch {app_name}.")

    # --- 6. Quick Information Queries ---

    def get_time(self) -> Tuple[bool, str]:
        now = datetime.now()
        time_str = now.strftime("%I:%M %p").lstrip("0")
        return (True, f"It is {time_str}.")

    def get_date(self) -> Tuple[bool, str]:
        now = datetime.now()
        date_str = now.strftime("%A, %B %d, %Y")
        return (True, f"Today is {date_str}.")

    def get_battery(self) -> Tuple[bool, str]:
        # Inspect /sys/class/power_supply
        base_dir = "/sys/class/power_supply"
        if os.path.isdir(base_dir):
            for entry in os.listdir(base_dir):
                if entry.startswith("BAT"):
                    cap_file = os.path.join(base_dir, entry, "capacity")
                    status_file = os.path.join(base_dir, entry, "status")
                    if os.path.isfile(cap_file):
                        with open(cap_file, "r") as f:
                            cap = f.read().strip()
                        status = "discharging"
                        if os.path.isfile(status_file):
                            with open(status_file, "r") as f:
                                status = f.read().strip().lower()
                        return (True, f"Battery is at {cap} percent and {status}.")
        return (True, "System is running on continuous AC power.")

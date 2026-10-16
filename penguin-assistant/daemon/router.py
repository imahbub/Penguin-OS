"""Hybrid Intent Router for PenguinOS Voice Assistant.

Implements Tier-1 fast-path regex and rule-based matching (<5ms)
with parameter extraction, before falling back to local SLM / Search.
"""

import re
from typing import Dict, Any, Optional
from .dispatcher import ActionDispatcher


class IntentRouter:
    """Parses text input into actionable intents."""

    def __init__(self, dispatcher: ActionDispatcher):
        self.dispatcher = dispatcher

    def route_and_execute(self, text: str) -> Dict[str, Any]:
        """Routes text command and returns execution outcome."""
        clean_text = text.strip().lower()
        # Remove trailing punctuation
        clean_text = re.sub(r"[?!.,]+$", "", clean_text)

        # 1. Volume Controls
        m = re.match(r"^(?:set |change )?volume (?:to )?(\d+)%?$", clean_text)
        if m:
            val = int(m.group(1))
            ok, msg = self.dispatcher.set_volume(val)
            return {"domain": "audio", "action": "set_volume", "success": ok, "response": msg}

        if re.match(r"^(?:increase volume|volume up|louder|turn it up)$", clean_text):
            ok, msg = self.dispatcher.change_volume(5)
            return {"domain": "audio", "action": "volume_up", "success": ok, "response": msg}

        if re.match(r"^(?:decrease volume|volume down|quieter|lower volume|turn it down)$", clean_text):
            ok, msg = self.dispatcher.change_volume(-5)
            return {"domain": "audio", "action": "volume_down", "success": ok, "response": msg}

        if re.match(r"^mute(?: audio| sound)?$", clean_text):
            ok, msg = self.dispatcher.set_mute("mute")
            return {"domain": "audio", "action": "mute", "success": ok, "response": msg}

        if re.match(r"^unmute(?: audio| sound)?$", clean_text):
            ok, msg = self.dispatcher.set_mute("unmute")
            return {"domain": "audio", "action": "unmute", "success": ok, "response": msg}

        # 2. Display Brightness
        m = re.match(r"^(?:set |change )?brightness (?:to )?(\d+)%?$", clean_text)
        if m:
            val = int(m.group(1))
            ok, msg = self.dispatcher.set_brightness(val)
            return {"domain": "display", "action": "set_brightness", "success": ok, "response": msg}

        if re.match(r"^(?:increase brightness|brightness up|brighter)$", clean_text):
            ok, msg = self.dispatcher.change_brightness(10)
            return {"domain": "display", "action": "brightness_up", "success": ok, "response": msg}

        if re.match(r"^(?:decrease brightness|brightness down|dimmer)$", clean_text):
            ok, msg = self.dispatcher.change_brightness(-10)
            return {"domain": "display", "action": "brightness_down", "success": ok, "response": msg}

        # 3. Media Controls
        if re.match(r"^(?:play|pause|resume|play pause)(?: music| audio| media)?$", clean_text):
            ok, msg = self.dispatcher.media_play_pause()
            return {"domain": "media", "action": "play_pause", "success": ok, "response": msg}

        if re.match(r"^(?:next|next track|next song|skip|skip track)$", clean_text):
            ok, msg = self.dispatcher.media_next()
            return {"domain": "media", "action": "next", "success": ok, "response": msg}

        if re.match(r"^(?:previous|previous track|previous song|go back)$", clean_text):
            ok, msg = self.dispatcher.media_previous()
            return {"domain": "media", "action": "previous", "success": ok, "response": msg}

        # 4. Session & Power Management
        if re.match(r"^(?:lock|lock screen|lock the screen)$", clean_text):
            ok, msg = self.dispatcher.lock_screen()
            return {"domain": "system", "action": "lock", "success": ok, "response": msg}

        if re.match(r"^(?:suspend|sleep|put system to sleep)$", clean_text):
            ok, msg = self.dispatcher.suspend()
            return {"domain": "system", "action": "suspend", "success": ok, "response": msg}

        if re.match(r"^(?:reboot|restart|restart computer|restart system)$", clean_text):
            ok, msg = self.dispatcher.reboot()
            return {"domain": "system", "action": "reboot", "success": ok, "response": msg}

        if re.match(r"^(?:shutdown|power off|turn off computer)$", clean_text):
            ok, msg = self.dispatcher.poweroff()
            return {"domain": "system", "action": "poweroff", "success": ok, "response": msg}

        # 5. App Launching
        m = re.match(r"^(?:open|launch|start) (.+)$", clean_text)
        if m:
            target_app = m.group(1).strip()
            ok, msg = self.dispatcher.launch_app(target_app)
            return {"domain": "apps", "action": "launch", "success": ok, "response": msg}

        # 6. Informational Queries
        if re.match(r"^(?:what time is it|current time|tell me the time|time)$", clean_text):
            ok, msg = self.dispatcher.get_time()
            return {"domain": "info", "action": "time", "success": ok, "response": msg}

        if re.match(r"^(?:what(?:'s| is) the date|what day is it|today(?:'s)? date|date)$", clean_text):
            ok, msg = self.dispatcher.get_date()
            return {"domain": "info", "action": "date", "success": ok, "response": msg}

        if re.match(r"^(?:what is the )?battery(?: status| level| percentage)?$", clean_text):
            ok, msg = self.dispatcher.get_battery()
            return {"domain": "info", "action": "battery", "success": ok, "response": msg}

        # Tier 2/3 Unmatched: Pass to LLM / Web Search
        return {
            "domain": "unmatched",
            "action": "query",
            "text": text,
            "success": False,
            "response": f"I heard '{text}', but I don't know how to do that yet."
        }

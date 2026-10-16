# PenguinOS AI Voice Assistant (`penguin-assistant`)

A sub-second, local-first voice assistant daemon natively integrated into **PenguinOS** (Fedora Kinoite / bootc / OSTree / KDE Plasma 6).

## Highlights

- **Sub-10ms Deterministic Execution (Tier 1 Fast Path)**: Instant volume, brightness, media, power, and app launching via PipeWire (`wpctl`), `playerctl`, `brightnessctl`, and `logind`.
- **Immutable Root Compliance**: Resides under `/usr/bin/penguin-assistant` and `/usr/share/penguin-assistant/` while preserving root-read-only guarantees.
- **KDE Plasma Wayland Floating Overlay**: A translucent floating HUD rendered in PyQt6 with dynamic status indicators (`Listening`, `Transcribing`, `Executing`, `Speaking`).
- **Zero-Latency IPC**: Unix domain socket interface at `/run/user/<UID>/penguin-assistant.sock` supporting hotkey triggers (`Super + A`), manual CLI queries, and real-time state broadcasts.

## CLI Usage

```bash
# Check daemon status
penguin-assistant status

# Trigger listening immediately (bound to shortcut Super + A)
penguin-assistant trigger

# Execute an intent directly without voice
penguin-assistant exec "set volume to 60"
penguin-assistant exec "what time is it"
penguin-assistant exec "open craft launcher"

# Synthesize speech
penguin-assistant speak "Welcome to PenguinOS."

# Run the visual overlay HUD
penguin-assistant overlay
```

## Supported Voice / Text Commands

| Domain | Example Phrase | Underlying Action |
| :--- | :--- | :--- |
| **Audio** | *"Set volume to 50%"*, *"Louder"*, *"Mute"* | `wpctl set-volume @DEFAULT_AUDIO_SINK@ <val>%` |
| **Brightness** | *"Brightness 80%"*, *"Dimmer"*, *"Brighter"* | `brightnessctl set <val>%` |
| **Media** | *"Play"*, *"Pause"*, *"Next track"*, *"Skip"* | `playerctl play-pause`, `playerctl next` |
| **Apps** | *"Open Craft Launcher"*, *"Launch Steam"*, *"Open Telegram"* | Launches target desktop binary / Flatpak |
| **Session** | *"Lock screen"*, *"Suspend"*, *"Restart"*, *"Shutdown"* | `loginctl lock-session`, `systemctl suspend` |
| **Info** | *"What time is it"*, *"What is today's date"*, *"Battery"* | Real-time system queries |

## Systemd User Service Integration

The daemon runs unprivileged inside the user's desktop session:

- Unit: `/usr/lib/systemd/user/penguin-assistant.service`
- Overlay: `/usr/lib/systemd/user/penguin-assistant-overlay.service`
- Autostart enabled via `default.target.wants` and `graphical-session.target.wants`.

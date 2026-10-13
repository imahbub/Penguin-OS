# PenguinOS 1.0-alpha

**PenguinOS 1.0-alpha** is a resilient, consumer-ready, immutable Linux distribution built on a container-native base (`bootc` / OSTree / Fedora Kinoite) designed for productivity workstations and high-performance gaming.

## Core Features

- **Immutable Core:** Atomic deployments and automatic rollback via container-native `bootc` image.
- **KDE Plasma Workstation:** Modern Wayland-first desktop with dark theme, pre-configured layouts, and subpixel rendering.
- **Pre-Tuned Gaming & Media:** Full VA-API/VDPAU hardware decoding, complete FFmpeg & GStreamer codecs, 32-bit & 64-bit Vulkan drivers, MangoHud, Gamescope, and PipeWire.
- **Deep KDE Connect Integration:** Pre-configured firewall rules, autostart background daemon, tray indicator, and zero-touch discovery.
- **Silent Background Updates:** Automated background staging via `penguin-update.timer` and `bootc upgrade` with low system priority.
- **First-Boot Welcome:** Onboarding wizard to assist with quick pairing and hardware verification.

## Repository Layout

```
.
├── Containerfile                         # Base OCI/bootc image definition
├── recipe.yml                            # Declarative BlueBuild specification
├── build.sh                              # Local container image build script
├── build-iso.sh                          # Bootable installer ISO builder (bootc-image-builder)
├── system/
│   ├── penguin-update.service            # Background update service
│   └── penguin-update.timer              # Daily background timer
├── environment/
│   └── environment                       # System-wide Wayland & VA-API environment
├── skel/
│   └── .config/
│       ├── kdeglobals                    # Global BreezeDark theme & desktop defaults
│       └── autostart/                    # Autostart entries (KDE Connect, Penguin Welcome)
├── scripts/
│   └── penguin-welcome                   # First-boot onboarding script
├── .github/workflows/
│   └── build.yml                         # Automated CI pipeline
└── custom_linux_distribution_specification.md  # Architectural specification
```

## How to Build

### 1. Build the OCI Container Image
```bash
./build.sh
```

### 2. Build a Bootable ISO Installer
```bash
./build-iso.sh penguinos:latest ./output
```

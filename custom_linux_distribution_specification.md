# Project Specification: Custom Immutable Linux Distribution ("PenguinOS")

## 1. Executive Summary & Vision
This document outlines the technical specification, architectural blueprint, packaging pipeline, and agent implementation directives for **PenguinOS**: a resilient, consumer-ready, immutable Linux distribution designed for both productivity workstations and high-performance gaming.

### Core Tenets
* **Resilient & Immutable Foundation:** Atomic image-based updates prevent root corruption and dependency drift. Failures automatically roll back without user intervention.
* **GUI-First & Zero Friction:** Graphical onboarding, system configuration, and software management out of the box. No required terminal interaction for desktop tasks.
* **Pre-Tuned Media & Gaming Stack:** Built-in hardware decoding/encoding (VA-API/VDPAU), complete proprietary and royalty-free codecs, and hybrid GPU/Vulkan runtimes ready from first boot.
* **Seamless Multi-Device Continuity:** Deep, out-of-the-box integration of **KDE Connect** spanning network policies, lock screens, notifications, and shell shortcuts.
* **Transparent Background Lifecycle:** Automated, silent background staging of updates with low system impact and zero workflow interruption.

---

## 2. Architectural Blueprint

### 2.1 Base Operating System: Image-Based / Bootc Architecture
The system utilizes a container-native, bootable image base (such as Fedora Kinoite/Silverblue via `bootc` and `rpm-ostree` or openSUSE MicroOS via transactional snapshots):

* **Container-Native Roots:** The operating system is entirely defined as a declarative container image (`Containerfile` / OCI registry).
* **Root Filesystem:** Read-only (`/usr` and system binaries are mounted strictly read-only).
* **Mutable User State:** Confined strictly to `/var`, `/etc` (managed via 3-way merge policies during image rebases), and `/home`.
* **Atomic Deployments & A/B Rollback:** Updates are applied as staged deployments. If a boot attempt fails hardware or target checks, the bootloader (GRUB/systemd-boot with boot-counting watchdog) automatically falls back to the previous deployment pin.

```
┌─────────────────────────────────────────────────────────────────┐
│                       User Space & Apps                         │
│  ┌──────────────────────┐  ┌─────────────────────────────────┐  │
│  │   Flathub / Flatpak  │  │  Custom Distro User Repos       │  │
│  │   (Up-to-date GUI)   │  │  (Custom OBS/COPR/OCI Flatpaks) │  │
│  └──────────────────────┘  └─────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                   CLI / Development Toolboxes                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │   Distrobox / Podman (Isolated containerized toolchains)  │  │
│  └───────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                 Immutable Core Operating System                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │   bootc / OSTree Image (Signed, Read-Only, A/B Rollback)  │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Desktop Environment & Visual Identity (KDE Plasma)

### 3.1 GUI-First Desktop Customization
* **Desktop Environment:** KDE Plasma (Wayland-first session by default, with XWayland compatibility layer).
* **Shell Layout & Ergonomics:**
  * Pre-configured modern dock/floating panel with balanced spacing and adaptive transparency.
  * Uniform, cohesive iconography, cursor theme, and typography (e.g., Inter / Noto Sans) applied globally via `/etc/skel/.config/kdeglobals`.
  * Customized Application Launcher and KRunner pre-configured for instant file search, device commands, and web shortcuts (`Alt + Space`).
* **Wayland & Display Defaults:**
  * Fractional scaling enabled with subpixel font smoothing.
  * Variable Refresh Rate (Adaptive Sync / FreeSync / G-Sync) auto-enabled when supported monitors are detected.
  * Screen capture, recording, and remote desktop brokered natively via `xdg-desktop-portal-kde` and PipeWire.

### 3.2 First-Boot GUI Onboarding Wizard (`penguin-welcome`)
* Language, locale, and timezone setup.
* Connectivity check and quick Wi-Fi selection.
* Immediate KDE Connect pairing workflow (initiating discovery over local subnet and Bluetooth).
* One-click toggle for additional gaming launchers or proprietary enhancements.

---

## 4. Hardware Acceleration, Codecs & Gaming Stack

### 4.1 Graphics & Compute Runtimes
* **AMD / Intel GPUs:**
  * Modern Mesa stack (`radv`, `anv`) with full 32-bit and 64-bit Vulkan/OpenGL libraries.
  * Modern kernel display engines (`amdgpu`, `i915`, `xe`) enabled with default power-saving profiles.
* **NVIDIA GPUs:**
  * Pre-packaged proprietary drivers (`nvidia-driver`, `cuda`, `nv-codec-headers`) configured with Wayland modesetting enabled (`nvidia-drm.modeset=1`).
  * Prime offload environment scripts installed out of the box (`prime-run` wrapper available).
* **Gaming Pipeline:**
  * Pre-installed Vulkan utilities, MangoHud, and Gamescope.
  * 32-bit multilib libraries and Proton wine dependencies pre-baked into the image to support Steam and Wine Flatpaks seamlessly.

### 4.2 Comprehensive Codecs & Media Pipeline
* **Audio/Video Drivers:** PipeWire, WirePlumber, and low-latency audio profiles enabled by default.
* **Proprietary & Royalty-Free Media Codecs:**
  * Full FFmpeg builds containing H.264, H.265 (HEVC), VP9, AV1, AAC, and ProRes.
  * GStreamer plugins: `gstreamer1-plugins-good`, `gstreamer1-plugins-bad`, `gstreamer1-plugins-ugly`, and `gstreamer1-libav`.
* **Hardware Decoding:**
  * Complete VA-API and VDPAU packages (`intel-media-driver`, `libva-intel-driver`, `libva-mesa-driver`, `mesa-vdpau-drivers`).
  * System-wide browser hardware video acceleration pre-configured via `/etc/environment` (`MOZ_ENABLE_WAYLAND=1`, VA-API flags).

---

## 5. Automated Background Update System

Updates run completely in the background without modal interruptions, forced reboots, or user maintenance commands.

### 5.1 Update Lifecycle
* **Timers:** A systemd timer (`penguin-update.timer`) executes daily with a randomized jitter window.
* **Network & Power Gates:** Update tasks are suspended if the host is on a metered network or running on low battery (< 20%).
* **Phased Execution:**
  1. **Core Image Pull:** Executes `bootc upgrade` or `rpm-ostree upgrade --download-only` silently in the background.
  2. **Flatpak Update:** Runs `flatpak update -y --noninteractive` across system and user installations.
  3. **Verification:** Cryptographic signature check (via Cosign or GPG) ensures the fetched image is authenticated.
  4. **Staging:** The new OS image is mounted and prepared in an inactive deployment slot.
  5. **Notification:** A desktop notification indicates that updates have completed cleanly and will apply on the next system restart.

---

## 6. First-Class KDE Connect Integration

KDE Connect is treated as core system infrastructure rather than an isolated user application.

### 6.1 Network & Firewall Provisioning
* Firewall configurations (`firewalld` / `nftables`) permit KDE Connect traffic by default on trusted and home zones:
  * **Ports:** `1714:1764` UDP and `1714:1764` TCP.
* `avahi-daemon` (mDNS) enabled by default for zero-touch local network peer discovery.

### 6.2 Desktop Convergence Features
* **Auto-Start Daemon:** `kdeconnectd` managed as an active systemd user service (`systemd --user`).
* **System Tray:** Pre-pinned KDE Connect widget displaying paired device battery levels, connectivity status, and quick-ping actions.
* **File Integration:** Seamless integration in Dolphin under the "Places" sidebar for connected devices, with files routed directly to `~/Downloads/KDEConnect/`.
* **Clipboard & SMS Sync:** Two-way clipboard synchronization enabled out of the box with inline notification reply support for SMS.

---

## 7. Custom Package Pipeline & Continuous Delivery

A dedicated CI/CD pipeline tracks upstream releases, builds custom packages, and deploys fresh container images.

```
Upstream Projects / Git Releases
               │
               ▼
   GitHub Actions CI Tracker
               │
   ├── Build Custom Packages (RPM / Flatpak)
   ├── Run Automated Smoke & Headless Boot Tests (QEMU)
   └── Build & Sign OCI Image (Containerfile)
               │
               ▼
   OCI Container Registry (Quay.io / GitHub Packages)
               │
               ▼
   Client Devices (Background `bootc upgrade`)
```

* **Build Automation:** GitHub Actions / GitLab CI monitors custom repository manifests.
* **Automated Smoke Tests:** Every newly built container image boots headlessly in a virtualized QEMU instance to confirm `graphical.target` is reached and critical services are running.
* **Continuous Delivery:** Passing images are signed via Cosign and pushed directly to the distribution's OCI registry.

---

## 8. Build Agent Recipes & Manifests

Provide these concrete configuration files directly to your build agents.

### 8.1 Recipe: `Containerfile` (bootc Base Image)

```dockerfile
# Containerfile: Base image for PenguinOS
FROM quay.io/fedora-ostree-desktops/kinoite:latest

# 1. Enable Non-Free & RPM Fusion Repositories (Codecs, Drivers)
RUN rpm-ostree install --apply-live -y \
    https://mirrors.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm \
    https://mirrors.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-$(rpm -E %fedora).noarch.rpm

# 2. Install Complete Codecs, Media Stack & Hardware Acceleration
RUN rpm-ostree install -y \
    ffmpeg \
    gstreamer1-plugins-bad-freeworld \
    gstreamer1-plugins-ugly \
    gstreamer1-libav \
    intel-media-driver \
    libva-intel-driver \
    libva-mesa-driver \
    mesa-vdpau-drivers \
    libva-utils \
    vdpauinfo

# 3. Install Gaming, GPU Libraries & Core Runtimes
RUN rpm-ostree install -y \
    mesa-vulkan-drivers \
    mesa-vulkan-drivers.i686 \
    vulkan-tools \
    mangohud \
    gamescope \
    distrobox \
    podman \
    pipewire-utils

# 4. Install KDE Connect & Networking Essentials
RUN rpm-ostree install -y \
    kde-connect \
    avahi \
    firewalld

# 5. Configure Firewall for KDE Connect
RUN firewall-offline-cmd --zone=FedoraWorkstation --add-service=kde-connect && \
    firewall-offline-cmd --zone=trusted --add-service=kde-connect

# 6. Setup Automated Background Update Service
COPY ./system/penguin-update.service /etc/systemd/system/penguin-update.service
COPY ./system/penguin-update.timer /etc/systemd/system/penguin-update.timer
RUN systemctl enable penguin-update.timer && \
    systemctl enable avahi-daemon.service

# 7. Apply Custom Plasma Theme & Skel Overlays
COPY ./skel/. /etc/skel/
COPY ./environment/environment /etc/environment

# 8. Clean up packaging cache
RUN ostree container commit
```

### 8.2 Recipe: BlueBuild Specification (`recipe.yml`)

```yaml
# recipe.yml: BlueBuild recipe for declarative OSTree/bootc builds
name: penguinos
description: Resilient, immutable KDE Plasma distribution with gaming and multimedia pre-configured.
base-image: quay.io/fedora-ostree-desktops/kinoite
image-version: latest

modules:
  - type: rpm-ostree
    repos:
      - https://mirrors.rpmfusion.org/free/fedora/rpmfusion-free-release-%OS_VERSION%.noarch.rpm
      - https://mirrors.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-%OS_VERSION%.noarch.rpm
    install:
      # Multimedia & Codecs
      - ffmpeg
      - gstreamer1-plugins-bad-freeworld
      - gstreamer1-plugins-ugly
      - gstreamer1-libav
      - intel-media-driver
      - libva-mesa-driver
      - mesa-vdpau-drivers
      # Gaming & GPU
      - vulkan-tools
      - mangohud
      - gamescope
      - distrobox
      # System & KDE Connect
      - kde-connect
      - avahi

  - type: flatpak
    remotes:
      flathub: https://dl.flathub.org/repo/flathub.flatpakrepo
    install:
      - com.valvesoftware.Steam
      - org.mozilla.firefox

  - type: systemd
    system:
      enabled:
        - penguin-update.timer
        - avahi-daemon.service

  - type: files
    files:
      - source: usr/etc/skel
        destination: /etc/skel
      - source: usr/etc/environment
        destination: /etc/environment
```

### 8.3 Automation Units: Background Update Service

#### `/etc/systemd/system/penguin-update.service`
```ini
[Unit]
Description=PenguinOS Silent Background Update
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/bin/bootc upgrade
ExecStartPost=/usr/bin/flatpak update -y --noninteractive
Nice=19
IOSchedulingClass=idle
```

#### `/etc/systemd/system/penguin-update.timer`
```ini
[Unit]
Description=Daily PenguinOS Silent Background Update Timer

[Timer]
OnCalendar=*-*-* 04:00:00
RandomizedDelaySec=3600
Persistent=true

[Install]
WantedBy=timers.target
```

---

## 9. Implementation Checklist for Build Agents

* [ ] **Phase 1: Base Image Build**
  * Validate build of the `Containerfile` or BlueBuild `recipe.yml`.
  * Ensure full VA-API/VDPAU codec packages resolve without dependency errors.
* [ ] **Phase 2: Shell & Theming Delivery**
  * Populate `/etc/skel/.config/` with the default customized KDE panel configuration, widgets, and look-and-feel package.
  * Verify `kdeconnectd` launches upon first user login.
* [ ] **Phase 3: Hardware Verification**
  * Confirm hardware video decoding runs correctly on Intel and AMD test devices.
  * Validate 32-bit Vulkan drivers for Steam and Proton compatibility.
* [ ] **Phase 4: Network & Update Validation**
  * Verify `firewalld` automatically opens KDE Connect ports (`1714:1764` TCP/UDP).
  * Validate that `penguin-update.timer` runs silently and downloads image updates to an alternate boot slot.
* [ ] **Phase 5: ISO Generation**
  * Package the OCI container image into a bootable installer ISO using `bootc-image-builder`.

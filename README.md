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

---

## Download & Test PenguinOS

### 1. Download the ISO from Hugging Face

You can download the single, uncut bootable installer ISO directly from the Hugging Face Storage Bucket:

👉 **[Hugging Face Bucket: linuxhasan/penguinos](https://huggingface.co/buckets/linuxhasan/penguinos)**

#### Download via Terminal (`hf` CLI)

```bash
# 1. Install the Hugging Face Hub CLI with Xet support
pip install --upgrade "huggingface_hub[hf_xet]"

# 2. Download the ISO and checksum
hf cp hf://buckets/linuxhasan/penguinos/PenguinOS-1.0-alpha.iso ./PenguinOS-1.0-alpha.iso
hf cp hf://buckets/linuxhasan/penguinos/PenguinOS-1.0-alpha.iso.sha256 ./PenguinOS-1.0-alpha.iso.sha256

# 3. Verify integrity
sha256sum -c PenguinOS-1.0-alpha.iso.sha256
```

---

### 2. Boot via QEMU on Linux

To test the ISO in a virtualized environment with hardware acceleration on Linux:

#### Prerequisites
Install QEMU and UEFI (OVMF) firmware on your host system:

* **Fedora / RHEL:**
  ```bash
  sudo dnf install qemu-system-x86 edk2-ovmf
  ```
* **Ubuntu / Debian:**
  ```bash
  sudo apt install qemu-system-x86 ovmf
  ```
* **Arch Linux:**
  ```bash
  sudo pacman -S qemu-desktop edk2-ovmf
  ```

#### Step A: Create a Virtual Hard Disk
Create a virtual disk (minimum 30 GB recommended for Anaconda installation):

```bash
qemu-img create -f qcow2 penguinos-disk.qcow2 40G
```

#### Step B: Launch QEMU with UEFI and KVM

Run the virtual machine:

```bash
# Locate your distro's OVMF UEFI firmware file:
# Ubuntu/Debian: /usr/share/ovmf/OVMF.fd
# Fedora: /usr/share/edk2/ovmf/OVMF_CODE.fd
# Arch: /usr/share/edk2/x64/OVMF_CODE.fd
OVMF_PATH="/usr/share/ovmf/OVMF.fd"
[ -f "$OVMF_PATH" ] || OVMF_PATH="/usr/share/edk2/ovmf/OVMF_CODE.fd"
[ -f "$OVMF_PATH" ] || OVMF_PATH="/usr/share/edk2/x64/OVMF_CODE.fd"

qemu-system-x86_64 \
  -enable-kvm \
  -m 4G \
  -smp 4 \
  -cpu host \
  -bios "$OVMF_PATH" \
  -cdrom PenguinOS-1.0-alpha.iso \
  -drive file=penguinos-disk.qcow2,if=virtio \
  -vga virtio \
  -display default,show-cursor=on \
  -device intel-hda -device hda-duplex \
  -net nic,model=virtio -net user
```

> [!TIP]
> After completing the Anaconda graphical installation inside QEMU, restart without the `-cdrom PenguinOS-1.0-alpha.iso` parameter to boot directly into your newly installed PenguinOS system:
> ```bash
> qemu-system-x86_64 \
>   -enable-kvm \
>   -m 4G \
>   -smp 4 \
>   -cpu host \
>   -bios "$OVMF_PATH" \
>   -drive file=penguinos-disk.qcow2,if=virtio \
>   -vga virtio \
>   -display default,show-cursor=on \
>   -device intel-hda -device hda-duplex \
>   -net nic,model=virtio -net user
> ```


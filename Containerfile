# Containerfile: Base image for PenguinOS
FROM quay.io/fedora-ostree-desktops/kinoite:43

# 1. Enable Non-Free & RPM Fusion Repositories (Codecs, Drivers)
RUN for i in 1 2 3 4 5; do \
        rpm-ostree install -y \
            https://mirrors.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm \
            https://mirrors.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-$(rpm -E %fedora).noarch.rpm && break || sleep 3; \
    done

# 2. Install Complete Codecs, Media Stack & Hardware Acceleration
RUN rpm-ostree override remove \
        mesa-va-drivers \
        libavcodec-free \
        libavdevice-free \
        libavfilter-free \
        libavformat-free \
        libavutil-free \
        libpostproc-free \
        libswresample-free \
        libswscale-free \
        ffmpeg-free \
        --install mesa-va-drivers-freeworld \
        --install ffmpeg && \
    rpm-ostree install -y \
        gstreamer1-plugins-bad-freeworld \
        gstreamer1-plugins-ugly \
        gstreamer1-libav \
        intel-media-driver \
        libva-intel-driver \
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

# 4. Install Drawing Tablet Drivers (Huion, Wacom) & Input Framework
RUN rpm-ostree install -y \
    xorg-x11-drv-wacom \
    libwacom \
    kcm_wacomtablet \
    fcitx5 \
    fcitx5-configtool \
    kcm-fcitx5

# 5. Install OpenBangla Keyboard (Copr repository)
RUN curl -fsSL -o /etc/yum.repos.d/_copr:copr.fedorainfracloud.org:badshah:openbangla-keyboard.repo \
        https://copr.fedorainfracloud.org/coprs/badshah/openbangla-keyboard/repo/fedora-43/badshah-openbangla-keyboard-fedora-43.repo && \
    rpm-ostree install -y fcitx-openbangla

# 6. Install Android App Subsystem (Waydroid)
RUN rpm-ostree install -y waydroid

# 7. Install KDE Connect & Networking Essentials
RUN rpm-ostree install -y \
    kde-connect \
    avahi \
    firewalld

# 8. Configure Firewall Policies (KDE Connect & Waydroid)
RUN if command -v firewall-offline-cmd >/dev/null 2>&1; then \
        firewall-offline-cmd --zone=FedoraWorkstation --add-service=kde-connect || true; \
        firewall-offline-cmd --zone=trusted --add-service=kde-connect || true; \
        firewall-offline-cmd --zone=trusted --add-interface=waydroid0 || true; \
    fi

# 9. Build and Install storytold/craft-launcher
RUN dnf install -y git cargo rust libxkbcommon-devel wayland-devel libX11-devel libXrandr-devel libXi-devel mesa-libGL-devel && \
    git clone --depth 1 https://github.com/storytold/craft-launcher.git /tmp/craft-launcher && \
    cd /tmp/craft-launcher && \
    cargo build --release && \
    cp target/release/artcraft-launcher /usr/local/bin/craft-launcher || cp target/release/craft-launcher /usr/local/bin/craft-launcher || true && \
    chmod +x /usr/local/bin/craft-launcher || true && \
    rm -rf /tmp/craft-launcher && \
    dnf remove -y cargo rust libxkbcommon-devel wayland-devel libX11-devel libXrandr-devel libXi-devel mesa-libGL-devel && \
    dnf clean all

# 10. Setup Automated Background Update Service & Utilities
COPY ./system/penguin-update.service /etc/systemd/system/penguin-update.service
COPY ./system/penguin-update.timer /etc/systemd/system/penguin-update.timer
COPY ./scripts/penguin-welcome /usr/local/bin/penguin-welcome
RUN chmod +x /usr/local/bin/penguin-welcome && \
    systemctl enable penguin-update.timer && \
    systemctl enable avahi-daemon.service && \
    systemctl enable waydroid-container.service

# 7. Apply Custom Plasma Theme, Skel Overlays & Environment
COPY ./skel/. /etc/skel/
COPY ./environment/environment /etc/environment

# 8. Apply PenguinOS Brand Identity (os-release, logo, wallpapers)
COPY ./branding/os-release /usr/lib/os-release
COPY ./branding/os-release /etc/os-release
COPY ./branding/icons/penguinos-logo.svg /usr/share/pixmaps/penguinos-logo.svg
COPY ./branding/icons/penguinos-logo.svg /usr/share/icons/hicolor/scalable/apps/penguinos-logo.svg
COPY ./branding/wallpapers/ /usr/share/wallpapers/

# 9. Clean up packaging cache
RUN ostree container commit

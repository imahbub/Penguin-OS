# Containerfile: Base image for PenguinOS
FROM quay.io/fedora-ostree-desktops/kinoite:43

# 1. Enable Non-Free & RPM Fusion Repositories (Codecs, Drivers)
RUN rpm-ostree install -y \
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
RUN if command -v firewall-offline-cmd >/dev/null 2>&1; then \
        firewall-offline-cmd --zone=FedoraWorkstation --add-service=kde-connect || true; \
        firewall-offline-cmd --zone=trusted --add-service=kde-connect || true; \
    fi

# 6. Setup Automated Background Update Service & Utilities
COPY ./system/penguin-update.service /etc/systemd/system/penguin-update.service
COPY ./system/penguin-update.timer /etc/systemd/system/penguin-update.timer
COPY ./scripts/penguin-welcome /usr/local/bin/penguin-welcome
RUN chmod +x /usr/local/bin/penguin-welcome && \
    systemctl enable penguin-update.timer && \
    systemctl enable avahi-daemon.service

# 7. Apply Custom Plasma Theme & Skel Overlays & Environment
COPY ./skel/. /etc/skel/
COPY ./environment/environment /etc/environment

# 8. Clean up packaging cache
RUN ostree container commit

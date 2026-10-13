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

# 3. Install Gaming, GPU Libraries, Core Runtimes & Desktop Apps
RUN rpm-ostree install -y \
    mesa-vulkan-drivers \
    mesa-vulkan-drivers.i686 \
    vulkan-tools \
    mangohud \
    gamescope \
    distrobox \
    podman \
    pipewire-utils \
    telegram-desktop

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

# 9. Install storytold/craft-launcher (Official linux-x86_64 release with complete assets)
RUN mkdir -p /tmp/craft-launcher && \
    curl -fsSL https://github.com/storytold/craft-launcher/releases/download/v0.3.2/artcraft-launcher-0.3.2-linux-x86_64.tar.gz | tar -xz -C /tmp/craft-launcher --strip-components=1 && \
    cp /tmp/craft-launcher/bin/artcraft-launcher /usr/local/bin/craft-launcher && \
    cp /tmp/craft-launcher/bin/artcraft-launcher /usr/bin/craft-launcher && \
    cp /tmp/craft-launcher/bin/artcraft-launcher /usr/bin/artcraft-launcher && \
    chmod 755 /usr/local/bin/craft-launcher /usr/bin/craft-launcher /usr/bin/artcraft-launcher && \
    cp -r /tmp/craft-launcher/share/icons/* /usr/share/icons/ && \
    cp -r /tmp/craft-launcher/share/icons/hicolor/scalable/apps/ai.storyteller.artcraft-launcher.svg /usr/share/icons/hicolor/scalable/apps/craft-launcher.svg || true && \
    cp -r /tmp/craft-launcher/share/icons/hicolor/512x512/apps/ai.storyteller.artcraft-launcher.png /usr/share/pixmaps/craft-launcher.png || true && \
    cp /tmp/craft-launcher/share/applications/ai.storyteller.artcraft-launcher.desktop /usr/share/applications/craft-launcher.desktop && \
    sed -i 's|Exec=.*|Exec=/usr/local/bin/craft-launcher|g' /usr/share/applications/craft-launcher.desktop && \
    sed -i 's|Icon=.*|Icon=craft-launcher|g' /usr/share/applications/craft-launcher.desktop && \
    rm -rf /tmp/craft-launcher

# 10. Configure Default Panel Launchers in Plasma layout template
RUN if [ -f /usr/share/plasma/layout-templates/org.kde.plasma.desktop.defaultPanel/contents/layout.js ]; then \
        sed -i 's|preferred://browser|preferred://browser,applications:craft-launcher.desktop|g' \
            /usr/share/plasma/layout-templates/org.kde.plasma.desktop.defaultPanel/contents/layout.js || true; \
    fi

# 11. Setup Services, Utilities & Scripts
COPY ./system/penguin-update.service /etc/systemd/system/penguin-update.service
COPY ./system/penguin-update.timer /etc/systemd/system/penguin-update.timer
COPY ./system/penguin-firstboot-flatpaks.service /etc/systemd/system/penguin-firstboot-flatpaks.service
COPY ./scripts/penguin-welcome /usr/local/bin/penguin-welcome
COPY ./scripts/penguin-pin-taskbar /usr/local/bin/penguin-pin-taskbar
COPY ./scripts/penguin-launch-app /usr/local/bin/penguin-launch-app
COPY ./scripts/penguin-install-apps /usr/local/bin/penguin-install-apps
RUN chmod +x /usr/local/bin/penguin-welcome /usr/local/bin/penguin-pin-taskbar /usr/local/bin/penguin-launch-app /usr/local/bin/penguin-install-apps && \
    systemctl enable penguin-update.timer && \
    systemctl enable penguin-firstboot-flatpaks.service && \
    systemctl enable avahi-daemon.service && \
    systemctl enable waydroid-container.service

# 12. Apply Custom Plasma Theme, Skel Overlays, SDDM & Environment
COPY ./skel/. /etc/skel/
COPY ./environment/environment /etc/environment
COPY ./environment/xdg/kcm-about-distrorc /etc/xdg/kcm-about-distrorc
COPY ./environment/sddm/10-theme.conf /etc/sddm.conf.d/10-theme.conf
RUN mkdir -p /usr/share/sddm/themes/breeze/
COPY ./environment/sddm/theme.conf.user /usr/share/sddm/themes/breeze/theme.conf.user

# 13. Apply PenguinOS Brand Identity (os-release, logos, wallpapers, boot splash)
COPY ./branding/os-release /usr/lib/os-release
COPY ./branding/os-release /etc/os-release
COPY ./branding/icons/penguinos-logo.svg /usr/share/pixmaps/penguinos-logo.svg
COPY ./branding/icons/penguinos-logo.png /usr/share/pixmaps/penguinos-logo.png
COPY ./branding/icons/penguinos-logo.svg /usr/share/icons/hicolor/scalable/apps/penguinos-logo.svg
COPY ./branding/icons/penguinos-logo.png /usr/share/icons/hicolor/512x512/apps/penguinos-logo.png
COPY ./branding/icons/*.png /usr/share/pixmaps/
COPY ./branding/icons/*.png /usr/share/icons/hicolor/128x128/apps/
COPY ./branding/wallpapers/ /usr/share/wallpapers/

# Replace Fedora branding in pixmaps, icons, plymouth boot splash, and anaconda
RUN for d in /usr/share/pixmaps /usr/share/icons /usr/share/plymouth/themes /usr/share/plymouth/themes/spinner /usr/share/plymouth/themes/bgrt /usr/share/anaconda/pixmaps; do \
        [ -d "$d" ] || continue; \
        find "$d" -type f \( -name "*fedora*" -o -name "watermark.png" -o -name "bgrt-fallback.png" \) | while read -r f; do \
            case "$f" in \
                *.svg) cp -f /usr/share/pixmaps/penguinos-logo.svg "$f" 2>/dev/null || true ;; \
                *.png) cp -f /usr/share/pixmaps/penguinos-logo.png "$f" 2>/dev/null || true ;; \
            esac; \
        done; \
    done

# 14. Clean up packaging cache
RUN ostree container commit

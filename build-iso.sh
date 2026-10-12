#!/usr/bin/env bash
# Package PenguinOS into a bootable installer ISO using bootc-image-builder
set -euo pipefail

IMAGE_NAME="${1:-penguinos:latest}"
OUTPUT_DIR="${2:-$(pwd)/output}"

mkdir -p "${OUTPUT_DIR}"

echo "==> Building bootable ISO from ${IMAGE_NAME}..."
echo "==> Output directory: ${OUTPUT_DIR}"

# Run bootc-image-builder
sudo docker run \
    --rm \
    --privileged \
    -v /var/lib/containers/storage:/var/lib/containers/storage \
    -v "$(pwd)/config.toml:/config.toml:ro" \
    -v "${OUTPUT_DIR}":/output \
    quay.io/centos-bootc/bootc-image-builder:latest \
    --type anaconda-iso \
    --rootfs btrfs \
    --config /config.toml \
    "${IMAGE_NAME}"

echo "==> ISO Generation finished successfully in ${OUTPUT_DIR}"

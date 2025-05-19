# Use Raspberry Pi 5 64-bit OS with Python (Debian Bookworm)
FROM balenalib/raspberrypi5-debian-python:3.10-bookworm

# Enable udev for device access
ENV UDEV=1

# Install only minimal system dependencies for EGLFS and audio
RUN apt-get update && apt-get install -y --no-install-recommends \
    libxkbcommon0 \
    libinput10 \
    libevdev2 \
    libegl1-mesa \
    libgl1-mesa-dri \
    libgbm1 \
    libdrm2 \
    libpulse0 \
    libfontconfig1 \
    libgl1 \
    libdouble-conversion3 \
    libxcb-cursor0 \
    xserver-xorg \
    xinit \
    x11-xserver-utils \
    x11-apps \
    gstreamer1.0-tools \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    gstreamer1.0-pulseaudio \
    gstreamer1.0-alsa \
    gstreamer1.0-x \
    gstreamer1.0-gl \
    alsa-utils \
    pulseaudio \
    && rm -rf /var/lib/apt/lists/*

# Xorg DRM config for Raspberry Pi HDMI output
RUN mkdir -p /etc/X11/xorg.conf.d && \
    echo 'Section "Device"\n  Identifier "HDMI"\n  Driver "modesetting"\n  Option "kmsdev" "/dev/dri/card0"\nEndSection' > /etc/X11/xorg.conf.d/99-pi-drm.conf

# NOTE: The following overlays must be set in /boot/config.txt on the host OS, not in Docker.
# Documented here for reference:
#   dtparam=i2c_arm=on
#   dtoverlay=waveshare-4dpic-3b
#   dtoverlay=waveshare-4dpic-4b
#   dtoverlay=waveshare-4dpic-5b

# Set Qt environment variables for X11
ENV QT_QPA_PLATFORM=xcb
ENV QT_DEBUG_PLUGINS=1
ENV LD_LIBRARY_PATH=/usr/lib/aarch64-linux-gnu:$LD_LIBRARY_PATH

# Set working directory
WORKDIR /usr/src/app

# Copy requirements and install Python dependencies
COPY bhoutgate/requirements.txt .
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir --root-user-action=ignore wheel setuptools && \
    pip3 install --no-cache-dir --root-user-action=ignore -r requirements.txt && \
    pip3 install --no-cache-dir --root-user-action=ignore PySide6==6.5.3

# Copy application code
COPY bhoutgate/ .

# Set the entrypoint to run main script
CMD ["sh", "-c", "rm -f /tmp/.X0-lock && Xorg :0 & sleep 2 && DISPLAY=:0 python3 main.py"] 
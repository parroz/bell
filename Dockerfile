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
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-render-util0 \
    libxcb-xinerama0 \
    libxcb-xfixes0 \
    libxcb-shape0 \
    libxcb-shm0 \
    libxcb-randr0 \
    libxcb-xkb1 \
    libx11-xcb1 \
    libxcb-util1 \
    libxcomposite1 \
    libxcursor1 \
    libxi6 \
    libxrandr2 \
    libxss1 \
    libxtst6 \
    libxv1 \
    libxinerama1 \
    libxkbcommon-x11-0 \
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

# Install all required GStreamer plugins, X11 utilities, and audio support for 800x480 HDMI video playback
RUN apt-get update && apt-get install -y --no-install-recommends \
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
    x11-apps \
    x11-xserver-utils \
    && rm -rf /var/lib/apt/lists/*

# Tested working pipeline for 800x480 HDMI:
# gst-launch-1.0 filesrc location=/usr/src/app/config/static/video.mp4 ! decodebin ! videoconvert ! videoscale ! video/x-raw,width=800,height=480 ! glimagesink

# Xorg DRM config for Raspberry Pi HDMI output
RUN mkdir -p /etc/X11/xorg.conf.d && \
    echo 'Section "Device"\n  Identifier "HDMI"\n  Driver "modesetting"\n  Option "kmsdev" "/dev/dri/card0"\nEndSection' > /etc/X11/xorg.conf.d/99-pi-drm.conf

# NOTE: The following overlays must be set in /boot/config.txt on the host OS, not in Docker.
# Documented here for reference:
#   dtparam=i2c_arm=on
#   dtoverlay=waveshare-4dpic-3b
#   dtoverlay=waveshare-4dpic-4b
#   dtoverlay=waveshare-4dpic-5b

# Start PulseAudio, Xorg (removing /tmp/.X0-lock if present), and then the app
CMD ["sh", "-c", "rm -f /tmp/.X0-lock; pgrep Xorg || (Xorg :0 & sleep 2); DISPLAY=:0 python3 main.py"]

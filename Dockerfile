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
    && rm -rf /var/lib/apt/lists/*

# Set Qt environment variables for EGLFS
ENV QT_QPA_PLATFORM=eglfs
ENV QT_DEBUG_PLUGINS=1
ENV LD_LIBRARY_PATH=/usr/lib/aarch64-linux-gnu:$LD_LIBRARY_PATH

# Set working directory
WORKDIR /usr/src/app

# Copy requirements and install Python dependencies
COPY bhoutgate/requirements.txt .
RUN pip3 install --no-cache-dir --root-user-action --upgrade pip && \
    pip3 install --no-cache-dir --root-user-action wheel setuptools && \
    pip3 install --no-cache-dir --root-user-action -r requirements.txt && \
    pip3 install --no-cache-dir --root-user-action PySide6==6.5.3


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

# Start PulseAudio, Xorg, and then the app
CMD ["sh", "-c", "sleep 3600"]

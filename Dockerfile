# Use Raspberry Pi 5 64-bit OS with Python (Debian Bookworm)
FROM balenalib/raspberrypi5-debian-python:3.10-bookworm

# Enable udev for device access
ENV UDEV=1

# Install X11, xcb, and font libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    xserver-xorg \
    xinit \
    libx11-6 \
    libxext6 \
    libxrender1 \
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
    libgl1-mesa-glx \
    libdouble-conversion3 \
    libxcb-cursor0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-shape0 \
    libxcb-shm0 \
    libxcb-sync1 \
    libxcb-xfixes0 \
    libxcb-xinerama0 \
    libxcb-xkb1 \
    libxkbcommon-x11-0 \
    xfonts-base xfonts-100dpi xfonts-75dpi \
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

# Set Qt environment variables for X11
ENV QT_QPA_PLATFORM=xcb
ENV QT_DEBUG_PLUGINS=1
ENV LD_LIBRARY_PATH=/usr/local/lib/python3.10/site-packages/PySide6/Qt/lib

# Create Xorg config for modesetting
RUN mkdir -p /etc/X11/xorg.conf.d && \
    printf 'Section "Device"\n    Identifier "Card0"\n    Driver "modesetting"\n    Option "kmsdev" "/dev/dri/card0"\nEndSection\n' > /etc/X11/xorg.conf.d/10-docker.conf

# Set working directory
WORKDIR /usr/src/app

# Copy requirements and install Python dependencies
COPY bhoutgate/requirements.txt .
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir --root-user-action=ignore wheel setuptools && \
    pip3 install --no-cache-dir --root-user-action=ignore -r requirements.txt && \
    pip3 install --no-cache-dir --root-user-action=ignore "PySide6==6.5.3"

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
CMD ["sh", "-c", "pulseaudio --start && Xorg :0 & sleep 2 && DISPLAY=:0 python3 main.py"] 
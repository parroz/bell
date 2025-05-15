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
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    gstreamer1.0-pulseaudio \
    pulseaudio \
    gstreamer1.0-tools \
    && rm -rf /var/lib/apt/lists/*
   
CMD ["sh", "-c", "pulseaudio --start && Xorg :0 & sleep 2 && DISPLAY=:0 python3 main.py"]
   
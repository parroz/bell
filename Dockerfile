# Force rebuild: 2024-05-15
# Use Raspberry Pi 5 64-bit OS with Python (Debian Bookworm)
FROM balenalib/raspberrypi5-debian-python:3.10-bookworm

# Enable udev for device access
ENV UDEV=1

# Install minimal system dependencies for X11 and Qt
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
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /usr/lib/aarch64-linux-gnu/libQt6*

# Set Qt environment variables for X11
ENV QT_QPA_PLATFORM=xcb
ENV QT_DEBUG_PLUGINS=1
ENV LD_LIBRARY_PATH=/usr/local/lib/python3.10/site-packages/PySide6/Qt/lib

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

# Set the entrypoint to run main script
CMD ["sh", "-c", "Xorg :0 & sleep 2 && DISPLAY=:0 python3 main.py"] 
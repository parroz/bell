# Use Raspberry Pi 5 64-bit OS with Python (Debian Bookworm)
FROM balenalib/raspberrypi5-debian-python:3.10-bookworm

# Enable udev for device access
ENV UDEV=1

# Install system dependencies for EGLFS, audio, and Qt6
RUN apt-get update && apt-get install -y --no-install-recommends \
    libxkbcommon0 \
    libinput10 \
    libevdev2 \
    libegl1-mesa \
    libgl1-mesa-dri \
    libgbm1 \
    libdrm2 \
    libpulse0 \
    qt6-base-dev \
    qt6-declarative-dev \
    qt6-wayland \
    qt6-virtualkeyboard-plugin \
    qt6-qpa-plugins \
    libqt6gui6 \
    && rm -rf /var/lib/apt/lists/*

# Set Qt environment variables for EGLFS
ENV QT_QPA_PLATFORM=eglfs
ENV QT_DEBUG_PLUGINS=1
ENV LD_LIBRARY_PATH=/usr/lib/aarch64-linux-gnu:$LD_LIBRARY_PATH
ENV QT_QPA_PLATFORM_PLUGIN_PATH=/usr/local/lib/python3.10/site-packages/PySide6/Qt/plugins/platforms

# Set working directory
WORKDIR /usr/src/app

# Copy requirements and install Python dependencies
COPY bhoutgate/requirements.txt .
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir wheel setuptools && \
    pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY bhoutgate/ .

# Set the entrypoint to run main script
CMD ["python3", "main.py"] 
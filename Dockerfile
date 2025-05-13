# Use Raspberry Pi 5 64-bit OS with Python (Debian Bullseye)
FROM balenalib/raspberrypi5-debian-python:3.10-bullseye

# Enable udev for device access
ENV UDEV=1

# Install system dependencies for EGLFS and Qt
RUN apt-get update && apt-get install -y --no-install-recommends \
    libxkbcommon0 \
    libinput10 \
    libevdev2 \
    libegl1-mesa \
    libgl1-mesa-dri \
    libgbm1 \
    libdrm2 \
    qtbase5-dev \
    qtbase5-dev-tools \
    libqt5gui5 \
    libqt5widgets5 \
    libqt5core5a \
    libqt5dbus5 \
    libqt5network5 \
    libqt5opengl5 \
    libqt5opengl5-dev \
    && rm -rf /var/lib/apt/lists/*

# Set Qt environment variables for EGLFS
ENV QT_QPA_PLATFORM=eglfs
ENV QT_DEBUG_PLUGINS=1
ENV LD_LIBRARY_PATH=/usr/lib/aarch64-linux-gnu:$LD_LIBRARY_PATH

# Set working directory
WORKDIR /usr/src/app

# Copy requirements and install Python dependencies
COPY bhoutgate/requirements.txt .
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir wheel setuptools && \
    pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY bhoutgate/ .

# Set the entrypoint to run test script
CMD ["python3", "test.py"] 
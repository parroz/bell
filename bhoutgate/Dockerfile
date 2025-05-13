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
    qt6-base-dev \
    qt6-base-dev-tools \
    libqt6gui6 \
    libqt6widgets6 \
    libqt6core6 \
    libqt6dbus6 \
    libqt6network6 \
    libqt6opengl6 \
    libqt6openglwidgets6 \
    && rm -rf /var/lib/apt/lists/*

# Set Qt environment variables for EGLFS
ENV QT_QPA_PLATFORM=eglfs
ENV QT_DEBUG_PLUGINS=1
ENV LD_LIBRARY_PATH=/usr/lib/aarch64-linux-gnu:$LD_LIBRARY_PATH

# Set working directory
WORKDIR /usr/src/app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir wheel setuptools && \
    pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set the entrypoint to run test script
CMD ["python3", "test.py"] 
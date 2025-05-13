FROM balenalib/raspberrypi5-debian-python:3.10-bullseye

# Enable udev for device access
ENV UDEV=1

# Install system dependencies for GUI and Qt
RUN apt-get update && apt-get install -y --no-install-recommends \
    libegl1-mesa \
    libgl1-mesa-dri \
    libgbm1 \
    libinput10 \
    libxkbcommon0 \
    libxcb-xinerama0 \
    libglu1-mesa \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-xfixes0 \
    libxcb-shape0 \
    libxcb-xkb1 \
    qt6-base-dev \
    qt6-base-dev-tools \
    libqt6gui6 \
    libqt6widgets6 \
    libqt6core6 \
    libqt6dbus6 \
    libqt6xcbqpa6 \
    libqt6network6 \
    libqt6opengl6 \
    libqt6openglwidgets6 \
    libqt6svg6 \
    libqt6svgwidgets6 \
    libqt6waylandclient6 \
    libqt6waylandcompositor6 \
    libqt6waylandeglclient6 \
    libqt6waylandeglcompositor6 \
    libqt6waylandserver6 \
    libqt6waylandtools6 \
    libqt6waylandwidgets6 \
    libqt6xcbqpa6 \
    libqt6xcbqpa-dev \
    libxcb1 \
    libxcb1-dev \
    libxcb-icccm4 \
    libxcb-icccm4-dev \
    libxcb-image0 \
    libxcb-image0-dev \
    libxcb-keysyms1 \
    libxcb-keysyms1-dev \
    libxcb-randr0 \
    libxcb-randr0-dev \
    libxcb-render-util0 \
    libxcb-render-util0-dev \
    libxcb-xfixes0 \
    libxcb-xfixes0-dev \
    libxcb-shape0 \
    libxcb-shape0-dev \
    libxcb-xkb1 \
    libxcb-xkb1-dev \
    && rm -rf /var/lib/apt/lists/*

# Set Qt environment variables
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

# Set the entrypoint
CMD ["python3", "main.py"] 
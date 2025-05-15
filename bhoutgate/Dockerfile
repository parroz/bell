FROM balenalib/raspberrypi5-debian-python:3.10-bullseye

# Enable udev for device access
ENV UDEV=on

# Force privileged mode recognition
ENV PRIVILEGED=true

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

# Create necessary directories
RUN mkdir -p config/static

# Copy certificates from local machine
COPY ../bhoutgate/config/static/ca.crt config/static/
COPY ../bhoutgate/config/static/client.crt config/static/
COPY ../bhoutgate/config/static/client.key config/static/

# Debug: List contents of config/static
RUN ls -la config/static/

# Copy application code
COPY . .

# Debug: List contents of config/static again
RUN ls -la config/static/

# Set the entrypoint to run Balena's entry script
ENTRYPOINT ["/usr/bin/entry.sh"]

# Set the command to run the test script
CMD ["python3", "main.py"] 
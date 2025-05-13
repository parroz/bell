FROM balenalib/raspberrypi5-debian-python:3.10-bullseye

# Enable udev for device access
ENV UDEV=1

# Install system dependencies for GUI and Qt
RUN apt-get update && apt-get install -y \
    xserver-xorg-core \
    xinit \
    matchbox-window-manager \
    x11-xserver-utils \
    xvfb \
    libxcb-xinerama0 \
    libglu1-mesa \
    libegl1-mesa \
    libgl1-mesa-dri \
    libgbm1 \
    libinput10 \
    libxkbcommon0 \
    libxkbcommon-x11-0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-xfixes0 \
    libxcb-shape0 \
    libxcb-xkb1 \
    && rm -rf /var/lib/apt/lists/*

# Set display for X11
ENV DISPLAY=:0
ENV QT_QPA_PLATFORM=xcb
ENV QT_DEBUG_PLUGINS=1

# Set working directory
WORKDIR /usr/src/app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir wheel setuptools && \
    pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create X server configuration
RUN echo 'Section "Device"\n\
    Identifier "Dummy Device"\n\
    Driver "dummy"\n\
EndSection\n\
\n\
Section "Monitor"\n\
    Identifier "Dummy Monitor"\n\
    HorizSync 28.0-80.0\n\
    VertRefresh 48.0-75.0\n\
EndSection\n\
\n\
Section "Screen"\n\
    Identifier "Dummy Screen"\n\
    Device "Dummy Device"\n\
    Monitor "Dummy Monitor"\n\
    DefaultDepth 24\n\
    SubSection "Display"\n\
        Depth 24\n\
        Modes "1024x768"\n\
    EndSubSection\n\
EndSection' > /usr/share/X11/xorg.conf.d/99-dummy.conf

# Create startup script
RUN echo '#!/bin/bash\n\
# Kill any existing X server\n\
pkill Xorg || true\n\
\n\
# Start X server with dummy driver\n\
Xvfb :0 -screen 0 1024x768x24 &\n\
sleep 3\n\
\n\
# Set display\n\
export DISPLAY=:0\n\
\n\
# Start window manager\n\
matchbox-window-manager &\n\
sleep 2\n\
\n\
# Start the application\n\
python3 main.py\n\
' > /usr/src/app/start.sh && \
    chmod +x /usr/src/app/start.sh

# Set the entrypoint
CMD ["/usr/src/app/start.sh"] 
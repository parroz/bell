# Use Raspberry Pi 5 64-bit OS with Python (Debian Bullseye)
FROM balenalib/raspberrypi5-debian-python:3.10-bullseye

# Install system dependencies for GUI and Qt
RUN apt-get update && \
    apt-get install -y --no-install-recommends --fix-missing \
    xserver-xorg-core \
    xinit \
    matchbox-window-manager \
    libgl1-mesa-dri \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libxcb-xinerama0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-xfixes0 \
    libxcb-shape0 \
    libxcb-xkb1 \
    libxcb-xinerama0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-xfixes0 \
    libxcb-shape0 \
    libxcb-xkb1 \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV UDEV=1
ENV DISPLAY=:0

# Set working directory
WORKDIR /usr/src/app

# Copy requirements first to leverage Docker cache
COPY bhoutgate/requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir wheel setuptools && \
    pip3 install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY bhoutgate/ .

# Create startup script
RUN echo '#!/bin/bash\n\
Xorg :0 -nolisten tcp &\n\
sleep 2\n\
matchbox-window-manager &\n\
sleep 2\n\
python3 main.py\n\
' > /usr/src/app/start.sh && \
chmod +x /usr/src/app/start.sh

# Start the application
CMD ["/usr/src/app/start.sh"] 
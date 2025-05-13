FROM balenalib/raspberrypi5-64-python:3.10-bullseye-run

# Enable udev for device access
ENV UDEV=1

# Install system dependencies for GUI and Qt
RUN apt-get update && apt-get install -y \
    xserver-xorg-core \
    xinit \
    matchbox-window-manager \
    x11-xserver-utils \
    libxcb-xinerama0 \
    libglu1-mesa \
    libegl1-mesa \
    libgl1-mesa-dri \
    libgbm1 \
    libinput10 \
    && rm -rf /var/lib/apt/lists/*

# Set display for X11
ENV DISPLAY=:0

# Set working directory
WORKDIR /usr/src/app

# Copy requirements and install Python dependencies
COPY bhoutgate/requirements.txt .
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir wheel setuptools && \
    pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY bhoutgate/ .

# Create startup script
RUN echo '#!/bin/bash\n\
Xorg :0 &\n\
sleep 2\n\
matchbox-window-manager -display :0 &\n\
python3 main.py' > /usr/src/app/start.sh && \
    chmod +x /usr/src/app/start.sh

# Set the entrypoint
CMD ["/usr/src/app/start.sh"] 
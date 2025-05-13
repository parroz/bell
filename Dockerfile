# Use Balena's recommended base image for Raspberry Pi 5 (64-bit)
FROM balenalib/raspberrypi5-64-python:3.11-bullseye

# Install system dependencies in smaller chunks with retries
RUN apt-get update && \
    apt-get install -y --no-install-recommends --fix-missing \
    libcamera0 \
    libcamera-apps-lite \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && \
    apt-get install -y --no-install-recommends --fix-missing \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && \
    apt-get install -y --no-install-recommends --fix-missing \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && \
    apt-get install -y --no-install-recommends --fix-missing \
    libatlas-base-dev \
    libgtk-3-dev \
    libcanberra-gtk3-module \
    && rm -rf /var/lib/apt/lists/*

# Install Tkinter dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends --fix-missing \
    python3-tk \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /usr/src/app

# Copy requirements first to leverage Docker cache
COPY bhoutgate/requirements.txt .

# Install Python dependencies with retry logic
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir wheel setuptools && \
    pip3 install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY bhoutgate/ .

# Set environment variables for Balena
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:0

# Start the application
CMD ["python3", "main.py"] 
FROM arm32v7/python:3.9-slim-buster

# Install system dependencies for Qt and git
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-venv \
    libgl1-mesa-glx \
    libglib2.0-0 \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Clone the repository
RUN git clone https://github.com/parroz/bell.git .

# Create requirements.txt
RUN echo "PySide6==6.6.1\npaho-mqtt==1.6.1\npython-dotenv==1.0.0" > /app/bhoutgate/frontend/requirements.txt

# Install Python dependencies
RUN cd bhoutgate/frontend && \
    pip3 install --no-cache-dir -r requirements.txt

# Set environment variables
ENV DISPLAY=:0
ENV PYTHONUNBUFFERED=1
ENV MQTT_BROKER=mqtt.bhout.com
ENV MQTT_PORT=8883

# Set working directory to frontend
WORKDIR /app/bhoutgate/frontend

# Create a test script to verify MQTT connectivity
RUN echo '#!/usr/bin/env python3\n\
import os\n\
import time\n\
import paho.mqtt.client as mqtt\n\
\n\
def on_connect(client, userdata, flags, rc):\n\
    print(f"Connected with result code {rc}")\n\
    client.subscribe("bhoutgate/test")\n\
\n\
def on_message(client, userdata, msg):\n\
    print(f"Received message on {msg.topic}: {msg.payload.decode()}")\n\
\n\
def test_mqtt():\n\
    broker = os.getenv("MQTT_BROKER", "localhost")\n\
    port = int(os.getenv("MQTT_PORT", "8883"))\n\
    \n\
    client = mqtt.Client()\n\
    client.on_connect = on_connect\n\
    client.on_message = on_message\n\
    \n\
    # Configure TLS\n\
    client.tls_set(\n\
        ca_certs="/app/bhoutgate/config/certs/ca.crt",\n\
        certfile="/app/bhoutgate/config/certs/client.crt",\n\
        keyfile="/app/bhoutgate/config/certs/client.key"\n\
    )\n\
    \n\
    print(f"Connecting to MQTT broker at {broker}:{port}")\n\
    client.connect(broker, port, 60)\n\
    \n\
    # Start the loop\n\
    client.loop_start()\n\
    \n\
    # Publish a test message\n\
    client.publish("bhoutgate/test", "Hello from container!")\n\
    \n\
    # Wait for messages\n\
    time.sleep(5)\n\
    \n\
    client.loop_stop()\n\
    client.disconnect()\n\
\n\
if __name__ == "__main__":\n\
    test_mqtt()\n\
' > /app/bhoutgate/frontend/test_mqtt.py

RUN chmod +x /app/bhoutgate/frontend/test_mqtt.py

# Run the application
CMD ["python3", "main.py"] 
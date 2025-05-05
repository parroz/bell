# BHOUTGate

A Raspberry Pi-based access control system with QR code scanning capabilities.

## Features

- QR code scanning for access control
- MQTT-based communication
- Secure TLS encryption
- Full-screen Qt-based interface
- Video playback for access granted/denied states
- Bell sound notification

## Project Structure

```
bhoutgate/
├── frontend/          # Qt-based frontend application
│   ├── main.py       # Main application code
│   ├── config.json   # Configuration file
│   └── static/       # Media files (video, sound, logo)
├── config/           # Configuration files
│   ├── mosquitto/    # MQTT broker configuration
│   └── certs/        # TLS certificates
└── README.md         # This file
```

## Setup

1. Install required packages:
```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv mosquitto mosquitto-clients
```

2. Create and activate a virtual environment:
```bash
cd bhoutgate/frontend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. Configure MQTT broker:
```bash
cd ../config/mosquitto
sudo cp mosquitto.conf /etc/mosquitto/conf.d/
sudo systemctl restart mosquitto
```

4. Start the frontend application:
```bash
cd ../../frontend
python main.py
```

## Configuration

The system is configured through the `frontend/config.json` file, which includes:
- MQTT broker settings
- TLS certificate paths
- Media file paths
- UI settings

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
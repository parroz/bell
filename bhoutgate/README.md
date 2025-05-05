# BHOUTGate Frontend

A Qt-based frontend application for the BHOUTGate access control system.

## Features

1. A full-screen Qt interface for displaying access control status
2. QR code scanning support
3. Video playback for access states
4. MQTT integration for communication
5. TLS encryption for security

## Requirements

- Python 3.8+
- PySide6
- paho-mqtt
- python-dotenv

## Installation

1. Create a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

1. Start the frontend application:
```bash
cd frontend
python main.py
```

The application will:
- Show a full-screen window
- Connect to the MQTT broker
- Display the configured video
- Handle QR code input
- Show access granted/denied states

## Configuration

The application is configured through `frontend/config.json`:

```json
{
    "mqtt": {
        "broker": "localhost",
        "port": 8883,
        "use_tls": true,
        "ca_cert": "/path/to/ca.crt",
        "client_cert": "/path/to/client.crt",
        "client_key": "/path/to/client.key",
        "topics": {
            "publish": "bhoutgate/scan_code",
            "subscribe": "bhoutgate/access_granted",
            "bell": "bhoutgate/bell/ring"
        }
    },
    "media": {
        "video_path": "/path/to/video.mp4",
        "bell_sound_path": "/path/to/bell.mp3",
        "logo_path": "/path/to/logo.png"
    },
    "ui": {
        "timeout_seconds": 5,
        "denial_display_time": 3
    }
}
```

## Project Structure

```
bhoutgate/
├── frontend/          # Qt frontend application
│   ├── main.py       # Main application code
│   ├── config.json   # Configuration file
│   └── static/       # Media files
├── config/           # Configuration files
│   ├── mosquitto/    # MQTT broker config
│   └── certs/        # TLS certificates
└── README.md         # This file
```

## Security Notes

- This is a local system designed to run offline
- For production use, consider implementing:
  - TLS/SSL for MQTT communication
  - Authentication for the configuration panel
  - Secure storage of certificates and keys 
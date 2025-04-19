# BHOUTGate - Gym Access Control System

BHOUTGate is a local gym access control system that runs fully offline. It consists of two main components:

1. A PyQt5 frontend application that runs on a touchscreen display
2. A Flask backend configuration panel

## Prerequisites

- Python 3.7 or higher
- MQTT broker (e.g., Mosquitto) running on localhost:1883
- Required Python packages (install using `pip install -r requirements.txt`)

## Installation

1. Clone this repository
2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Install and start an MQTT broker (e.g., Mosquitto)
4. Place your logo files in the `config/static/` directory:
   - `logo.png` - Static logo image
   - `logo.mp4` - Animated logo video

## Running the System

### 1. Start the Configuration Panel (Backend)

```bash
cd backend
python app.py
```

The configuration panel will be available at `http://localhost:8080`

### 2. Start the Frontend Application

```bash
cd frontend
python main.py
```

The frontend will run in fullscreen mode, showing the animated logo video when idle.

## Configuration

Use the web interface at `http://localhost:8080` to configure:

- MQTT topics for publishing and subscribing
- Timeout duration for access responses
- Upload logo files and certificates

## Testing

1. Start both the backend and frontend applications
2. In the frontend, click the "Simulate QR Scan" button
3. The system will publish a simulated QR code to the configured MQTT topic
4. To test access granted, publish "granted" to the configured response topic
5. To test access denied, publish any other message to the response topic

## File Structure

```
bhoutgate/
│
├── frontend/         # PyQt5 GUI app
│   └── main.py
│
├── backend/          # Flask config panel
│   └── app.py
│
├── config/           # Uploaded assets and settings
│   ├── settings.json
│   └── static/
│       ├── logo.png
│       ├── logo.mp4
│       ├── ca.crt
│       ├── client.crt
│       └── client.key
```

## Security Notes

- This is a local system designed to run offline
- For production use, consider implementing:
  - TLS/SSL for MQTT communication
  - Authentication for the configuration panel
  - Secure storage of certificates and keys 
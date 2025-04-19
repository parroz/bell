# BHOUTGate

A gate control system with MQTT integration and video display capabilities.

## Features

- MQTT integration for access control
- Video display support
- Web-based configuration interface
- Secure password protection
- File upload capabilities (logo, video, certificates)

## Project Structure

```
bhoutgate/
├── backend/           # Flask web server for configuration
├── frontend/          # PySide6-based display application
└── config/           # Configuration files and static content
    ├── static/       # Uploaded files (logo, video, certificates)
    └── settings.json # Application settings
```

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Start the backend server:
   ```bash
   cd bhoutgate/backend
   python app.py
   ```

4. Start the frontend display:
   ```bash
   cd bhoutgate/frontend
   python main.py
   ```

## Configuration

Access the configuration interface at `http://localhost:8080` and log in with the default password:
- Username: admin
- Password: admin

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
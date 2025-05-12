import sys
import json
import os
import ssl
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QLineEdit
from PySide6.QtCore import Qt, QTimer, QUrl, Signal, QObject
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtGui import QPixmap
import paho.mqtt.client as mqtt

class MQTTClient(QObject):
    message_received = Signal(str)
    connected = Signal()

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.client = None
        self.is_connected = False
        self.reconnect_timer = None
        self.setup_client()

    def setup_client(self):
        if self.client is not None:
            try:
                self.client.disconnect()
                self.client.loop_stop()
            except:
                pass
            self.client = None

        print("\n=== MQTT Client Setup ===")
        print(f"Creating new MQTT client instance")
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self.client.on_publish = self.on_publish
        
        try:
            print("\n=== TLS Configuration ===")
            print(f"CA cert path: {self.config['mqtt']['ca_cert']}")
            print(f"Client cert path: {self.config['mqtt']['client_cert']}")
            print(f"Client key path: {self.config['mqtt']['client_key']}")
            
            # Check if certificate files exist
            for cert_file in [self.config['mqtt']['ca_cert'], self.config['mqtt']['client_cert'], self.config['mqtt']['client_key']]:
                if not os.path.exists(cert_file):
                    print(f"WARNING: Certificate file does not exist: {cert_file}")
                else:
                    print(f"Certificate file exists: {cert_file}")
            
            self.client.tls_set(
                ca_certs=self.config['mqtt']['ca_cert'],
                certfile=self.config['mqtt']['client_cert'],
                keyfile=self.config['mqtt']['client_key'],
                cert_reqs=ssl.CERT_REQUIRED,
                tls_version=ssl.PROTOCOL_TLS,
                ciphers=None
            )
            self.client.tls_insecure_set(False)
            # Set the hostname for TLS verification
            self.client._hostname = self.config['mqtt']['broker']
            print("TLS configuration successful")
        except Exception as e:
            print(f"Error configuring TLS: {e}")
            raise
        
        try:
            print("\n=== MQTT Connection ===")
            broker = self.config['mqtt']['broker']
            port = self.config['mqtt']['port']
            print(f"Attempting to connect to MQTT broker at {broker}:{port}")
            self.client.connect(broker, port, 60)
            self.client.loop_start()
            print("MQTT client loop started")
        except Exception as e:
            print(f"Error connecting to MQTT broker: {e}")
            self.schedule_reconnect()

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT broker successfully")
            self.is_connected = True
            subscribe_topic = self.config['mqtt']['topics']['subscribe']
            print(f"Subscribing to topic: {subscribe_topic}")
            client.subscribe(subscribe_topic)
            self.connected.emit()
        else:
            print(f"Failed to connect to MQTT broker, return code: {rc}")
            self.is_connected = False
            self.schedule_reconnect()

    def on_publish(self, client, userdata, mid):
        print(f"Message published successfully (mid: {mid})")

    def on_disconnect(self, client, userdata, rc):
        print("Disconnected from MQTT broker")
        self.is_connected = False
        if rc != 0:
            self.schedule_reconnect()

    def schedule_reconnect(self):
        if self.reconnect_timer is not None:
            self.reconnect_timer.stop()
        
        self.reconnect_timer = QTimer()
        self.reconnect_timer.setSingleShot(True)
        self.reconnect_timer.timeout.connect(self.setup_client)
        self.reconnect_timer.start(5000)

    def on_message(self, client, userdata, msg):
        print(f"Received message on {msg.topic}: {msg.payload.decode()}")
        if msg.topic == self.config['mqtt']['topics']['subscribe']:
            self.message_received.emit(msg.payload.decode())

    def publish(self, topic, message):
        if not self.is_connected:
            print("Not connected to MQTT broker, cannot publish")
            return
        try:
            print(f"Publishing to {topic}: {message}")
            result = self.client.publish(topic, message, qos=1)
            print(f"Publish result: {result}")
            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                print(f"Error publishing message: {result.rc}")
                self.schedule_reconnect()
        except Exception as e:
            print(f"Error publishing message: {e}")
            self.schedule_reconnect()

class BHOUTGate(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BHOUTGate")
        
        # Initialize variables
        self.timeout_timer = None
        self.logo_label = None
        self.video_widget = None
        self.status_label = None
        
        # Load configuration
        self.load_config()
        
        # Setup UI first
        self.setup_ui()
        
        # Setup MQTT client
        self.mqtt_client = MQTTClient(self.config)
        self.mqtt_client.message_received.connect(self.handle_access_response)
        self.mqtt_client.connected.connect(self.on_mqtt_connected)
        
        # Initialize media players
        self.setup_media()
        
        # Setup QR scanner input
        self.qr_input = QLineEdit()
        self.qr_input.setReadOnly(True)
        self.qr_input.setVisible(False)
        self.qr_input.returnPressed.connect(self.handle_qr_input)
        
        # Show full screen after everything is set up
        self.showFullScreen()
        
        # Start in idle mode
        self.show_idle()
    
    def load_config(self):
        config_path = 'config.json'
        try:
            with open(config_path, 'r') as f:
                self.config = json.load(f)
                
            # Override MQTT broker settings with environment variables
            broker = os.getenv('MQTT_BROKER')
            port = os.getenv('MQTT_PORT')
            
            if broker:
                print(f"Overriding MQTT broker with environment variable: {broker}")
                self.config['mqtt']['broker'] = broker
            
            if port:
                print(f"Overriding MQTT port with environment variable: {port}")
                self.config['mqtt']['port'] = int(port)
            
            print(f"Final MQTT configuration: broker={self.config['mqtt']['broker']}, port={self.config['mqtt']['port']}")
        except Exception as e:
            print(f"Error loading config: {e}")
            raise
    
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create video widget
        self.video_widget = QVideoWidget()
        self.video_widget.setStyleSheet("background-color: black;")
        layout.addWidget(self.video_widget)
        
        # Create status label
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(self.status_label)
        
        # Create hidden QR input field
        self.qr_input = QLineEdit()
        self.qr_input.setReadOnly(True)
        self.qr_input.setVisible(False)
        self.qr_input.returnPressed.connect(self.handle_qr_input)
        layout.addWidget(self.qr_input)
        
        # Hide status initially
        self.status_label.hide()
    
    def setup_media(self):
        # Setup video player
        self.media_player = QMediaPlayer()
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.mediaStatusChanged.connect(self.handle_media_status)
        self.media_player.positionChanged.connect(self.handle_position_changed)
        self.media_player.durationChanged.connect(self.handle_duration_changed)
        
        # Setup audio player for bell sound
        self.audio_output = QAudioOutput()
        self.bell_player = QMediaPlayer()
        self.bell_player.setAudioOutput(self.audio_output)
        self.bell_player.mediaStatusChanged.connect(self.handle_bell_status)
        
        # Load and pause video initially
        video_path = self.config['media']['video_path']
        if os.path.exists(video_path):
            print(f"Loading video from: {video_path}")
            self.media_player.setSource(QUrl.fromLocalFile(video_path))
            self.media_player.pause()
            self.media_player.setPosition(0)
            print("Video loaded and paused")
        else:
            print("No video file configured or file not found")
    
    def show_idle(self):
        if self.timeout_timer and self.timeout_timer.isActive():
            self.timeout_timer.stop()
        self.timeout_timer = None
        
        self.media_player.pause()
        self.media_player.setPosition(0)
        
        self.status_label.hide()
        
        print("Returned to idle mode")
    
    def resizeEvent(self, event):
        if self.logo_label and self.logo_label.isVisible():
            logo_path = self.config['media']['logo_path']
            if os.path.exists(logo_path):
                pixmap = QPixmap(logo_path)
                scaled_pixmap = pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.logo_label.setPixmap(scaled_pixmap)
        super().resizeEvent(event)
    
    def mousePressEvent(self, event):
        if self.video_widget.isVisible() and not self.status_label.isVisible():
            self.play_animation()
    
    def play_animation(self):
        print("Starting animation")
        
        # Send MQTT message for bell ring
        bell_topic = self.config['mqtt']['topics']['bell']
        print(f"Publishing bell ring to {bell_topic}")
        self.mqtt_client.publish(bell_topic, "ring")
        
        # Play bell sound
        bell_path = self.config['media']['bell_sound_path']
        if os.path.exists(bell_path):
            self.bell_player.setSource(QUrl.fromLocalFile(bell_path))
            self.bell_player.play()
            print("Playing bell sound")
        
        # Play video animation
        print("Playing video")
        self.media_player.setPosition(0)
        self.media_player.play()
    
    def handle_duration_changed(self, duration):
        print(f"Video duration: {duration}ms")
        self.video_duration = duration
    
    def handle_position_changed(self, position):
        print(f"Video position: {position}ms")
        if hasattr(self, 'video_duration') and position >= self.video_duration - 100:
            print("Video completed one cycle, pausing")
            self.media_player.pause()
            self.media_player.setPosition(0)
    
    def handle_media_status(self, status):
        print(f"Media status changed: {status}")
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            print("Video ended")
            self.media_player.pause()
            self.media_player.setPosition(0)
    
    def handle_bell_status(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.bell_player.stop()
    
    def handle_access_response(self, response):
        if self.timeout_timer and self.timeout_timer.isActive():
            self.timeout_timer.stop()
        
        if response.lower() == "granted":
            self.play_animation()
        else:
            print(f"Access denied: {response}")
            self.show_denial_reason(response)
    
    def show_denial_reason(self, reason):
        print(f"Access denied: {reason}")
        
        self.status_label.setText(f"Access Denied\n{reason}")
        self.status_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: red;
            background-color: black;
            padding: 20px;
            border-radius: 10px;
        """)
        
        self.status_label.show()
        
        self.timeout_timer = QTimer()
        self.timeout_timer.setSingleShot(True)
        self.timeout_timer.timeout.connect(self.show_idle)
        self.timeout_timer.start(self.config['ui']['denial_display_time'] * 1000)

    def on_mqtt_connected(self):
        print("MQTT client connected and ready")
    
    def handle_qr_input(self):
        qr_data = self.qr_input.text()
        print(f"QR Code scanned: {qr_data}")
        
        # Format the message as JSON
        from datetime import datetime
        message = {
            "message": {
                "data": {
                    "type": "QRCode",
                    "data": qr_data,
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                }
            }
        }
        
        # Convert to JSON string
        import json
        json_message = json.dumps(message)
        print(f"Publishing message: {json_message}")
        
        self.mqtt_client.publish(self.config['mqtt']['topics']['publish'], json_message)
        self.qr_input.clear()
    
    def keyPressEvent(self, event):
        if event.key() != Qt.Key_Return and event.key() != Qt.Key_Enter:
            self.qr_input.setText(self.qr_input.text() + event.text())
        else:
            self.qr_input.returnPressed.emit()
    
    def closeEvent(self, event):
        super().closeEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = BHOUTGate()
    window.show()
    sys.exit(app.exec()) 
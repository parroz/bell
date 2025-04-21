import sys
import json
import os
import time
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import Qt, QTimer, QUrl, Signal, QObject
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtGui import QPixmap, QColor, QPalette
import paho.mqtt.client as mqtt

class MQTTClient(QObject):
    message_received = Signal(str)  # Signal to emit when a message is received
    connected = Signal()  # Signal to emit when connected

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.client = None
        self.is_connected = False
        self.reconnect_timer = None
        self.setup_client()

    def setup_client(self):
        """Setup MQTT client with proper configuration"""
        if self.client is not None:
            try:
                self.client.disconnect()
                self.client.loop_stop()
            except:
                pass
            self.client = None

        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self.client.on_publish = self.on_publish  # Add publish callback
        
        # Configure TLS if enabled
        if self.config.get('mqtt_use_tls', False):
            try:
                print("Configuring TLS for MQTT connection...")
                print(f"CA cert: {self.config.get('mqtt_ca_cert')}")
                print(f"Client cert: {self.config.get('mqtt_client_cert')}")
                print(f"Client key: {self.config.get('mqtt_client_key')}")
                
                self.client.tls_set(
                    ca_certs=self.config.get('mqtt_ca_cert'),
                    certfile=self.config.get('mqtt_client_cert'),
                    keyfile=self.config.get('mqtt_client_key'),
                    tls_version=mqtt.ssl.PROTOCOL_TLSv1_2
                )
                print("TLS configured successfully")
            except Exception as e:
                print(f"Error configuring TLS: {e}")
                raise
        
        # Connect to broker - FORCE port 8883 for TLS
        try:
            print(f"Connecting to MQTT broker at {self.config['mqtt_broker']}:8883")
            self.client.connect(self.config['mqtt_broker'], 8883, 60)
            self.client.loop_start()
        except Exception as e:
            print(f"Error connecting to MQTT broker: {e}")
            self.schedule_reconnect()

    def on_connect(self, client, userdata, flags, rc):
        """Callback for when the client receives a CONNACK response from the server"""
        if rc == 0:
            print("Connected to MQTT broker successfully")
            self.is_connected = True
            # Subscribe to the access granted topic
            subscribe_topic = self.config['mqtt_subscribe_topic']
            print(f"Subscribing to topic: {subscribe_topic}")
            client.subscribe(subscribe_topic)
            self.connected.emit()
        else:
            print(f"Failed to connect to MQTT broker, return code: {rc}")
            self.is_connected = False
            self.schedule_reconnect()

    def on_publish(self, client, userdata, mid):
        """Callback for when a message is published"""
        print(f"Message published successfully (mid: {mid})")

    def on_disconnect(self, client, userdata, rc):
        """Callback for when the client disconnects from the broker"""
        print("Disconnected from MQTT broker")
        self.is_connected = False
        if rc != 0:  # Only reconnect if the disconnect was unexpected
            self.schedule_reconnect()

    def schedule_reconnect(self):
        """Schedule a reconnection attempt using QTimer"""
        if self.reconnect_timer is not None:
            self.reconnect_timer.stop()
        
        self.reconnect_timer = QTimer()
        self.reconnect_timer.setSingleShot(True)
        self.reconnect_timer.timeout.connect(self.setup_client)
        self.reconnect_timer.start(5000)  # 5 seconds delay

    def on_message(self, client, userdata, msg):
        """Callback for when a message is received"""
        print(f"Received message on {msg.topic}: {msg.payload.decode()}")
        if msg.topic == self.config['mqtt_subscribe_topic']:
            self.message_received.emit(msg.payload.decode())

    def publish(self, topic, message):
        """Publish a message to the MQTT broker"""
        if not self.is_connected:
            print("Not connected to MQTT broker, cannot publish")
            return
        try:
            print(f"Publishing to {topic}: {message}")
            result = self.client.publish(topic, message, qos=1)  # Use QoS 1 for guaranteed delivery
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
        self.scan_button = None
        
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
        
        # Show full screen after everything is set up
        self.showFullScreen()
        
        # Start in idle mode
        self.show_idle()
    
    def load_config(self):
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'settings.json')
        try:
            with open(config_path, 'r') as f:
                self.config = json.load(f)
                # Ensure required settings exist
                if 'mqtt_publish_topic' not in self.config:
                    self.config['mqtt_publish_topic'] = 'bhoutgate/scan_code'
                if 'mqtt_subscribe_topic' not in self.config:
                    self.config['mqtt_subscribe_topic'] = 'bhoutgate/access_granted'
                if 'mqtt_bell_topic' not in self.config:
                    self.config['mqtt_bell_topic'] = 'bhoutgate/bell/ring'
                if 'timeout_seconds' not in self.config:
                    self.config['timeout_seconds'] = 5
                if 'bell_sound_path' not in self.config:
                    self.config['bell_sound_path'] = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', 'static', 'bell.mp3')
                if 'mqtt_use_tls' not in self.config:
                    self.config['mqtt_use_tls'] = True  # Enable TLS by default
                if 'mqtt_port' not in self.config:
                    self.config['mqtt_port'] = 8883  # Use TLS port by default
                if 'mqtt_broker' not in self.config:
                    self.config['mqtt_broker'] = 'localhost'
                
                # Get the absolute path to the workspace root
                workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                
                # Set certificate paths with correct directory structure
                self.config['mqtt_ca_cert'] = os.path.join(workspace_root, 'bhoutgate', 'config', 'certs', 'ca.crt')
                self.config['mqtt_client_cert'] = os.path.join(workspace_root, 'bhoutgate', 'config', 'certs', 'client.crt')
                self.config['mqtt_client_key'] = os.path.join(workspace_root, 'bhoutgate', 'config', 'certs', 'client.key')
                
                print(f"Loaded configuration: {self.config}")
                print(f"CA cert path: {self.config['mqtt_ca_cert']}")
                print(f"Client cert path: {self.config['mqtt_client_cert']}")
                print(f"Client key path: {self.config['mqtt_client_key']}")
                print(f"MQTT broker: {self.config['mqtt_broker']}:{self.config['mqtt_port']}")
        except Exception as e:
            print(f"Error loading config: {e}")
            # Get the absolute path to the workspace root
            workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            
            self.config = {
                'mqtt_broker': 'localhost',
                'mqtt_port': 8883,  # Use TLS port by default
                'mqtt_publish_topic': 'bhoutgate/scan_code',
                'mqtt_subscribe_topic': 'bhoutgate/access_granted',
                'mqtt_bell_topic': 'bhoutgate/bell/ring',
                'timeout_seconds': 5,
                'bell_sound_path': os.path.join(workspace_root, 'bhoutgate', 'config', 'static', 'bell.mp3'),
                'video_path': os.path.join(workspace_root, 'bhoutgate', 'config', 'static', 'video.mp4'),
                'mqtt_use_tls': True,  # Enable TLS by default
                'mqtt_ca_cert': os.path.join(workspace_root, 'bhoutgate', 'config', 'certs', 'ca.crt'),
                'mqtt_client_cert': os.path.join(workspace_root, 'bhoutgate', 'config', 'certs', 'client.crt'),
                'mqtt_client_key': os.path.join(workspace_root, 'bhoutgate', 'config', 'certs', 'client.key')
            }
    
    def setup_ui(self):
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        layout.setSpacing(0)  # Remove spacing
        
        # Create video widget
        self.video_widget = QVideoWidget()
        self.video_widget.setStyleSheet("background-color: black;")  # Set black background
        layout.addWidget(self.video_widget)
        
        # Create status label
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(self.status_label)
        
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
        video_path = self.config['video_path']
        if os.path.exists(video_path):
            print(f"Loading video from: {video_path}")  # Debug print
            self.media_player.setSource(QUrl.fromLocalFile(video_path))
            self.media_player.pause()
            self.media_player.setPosition(0)  # Start at beginning
            print("Video loaded and paused")  # Debug print
        else:
            print(f"Video file not found at: {video_path}")  # Debug print
    
    def show_idle(self):
        # Stop any active timers
        if self.timeout_timer and self.timeout_timer.isActive():
            self.timeout_timer.stop()
        self.timeout_timer = None
        
        # Pause video at beginning
        self.media_player.pause()
        self.media_player.setPosition(0)
        
        # Hide status
        self.status_label.hide()
        
        print("Returned to idle mode")  # Debug print
    
    def resizeEvent(self, event):
        # Only update logo if it exists and is visible
        if self.logo_label and self.logo_label.isVisible():
            logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', 'static', 'logo.png')
            if os.path.exists(logo_path):
                pixmap = QPixmap(logo_path)
                scaled_pixmap = pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.logo_label.setPixmap(scaled_pixmap)
        super().resizeEvent(event)
    
    def mousePressEvent(self, event):
        # Handle touch/click anywhere on the screen
        if self.video_widget.isVisible() and not self.status_label.isVisible():
            self.play_animation()
    
    def play_animation(self):
        print("Starting animation")  # Debug print
        
        # Send MQTT message for bell ring
        bell_topic = self.config['mqtt_bell_topic']
        if not bell_topic.startswith('bhoutgate/'):
            bell_topic = f"bhoutgate/{bell_topic.lstrip('/')}"
        print(f"Publishing bell ring to {bell_topic}")  # Debug print
        self.mqtt_client.publish(bell_topic, "ring")
        
        # Play bell sound
        bell_path = self.config['bell_sound_path']
        if os.path.exists(bell_path):
            self.bell_player.setSource(QUrl.fromLocalFile(bell_path))
            self.bell_player.play()
            print("Playing bell sound")  # Debug print
        
        # Play video animation
        print("Playing video")  # Debug print
        self.media_player.setPosition(0)  # Reset to beginning
        self.media_player.play()
    
    def handle_duration_changed(self, duration):
        print(f"Video duration: {duration}ms")  # Debug print
        self.video_duration = duration
    
    def handle_position_changed(self, position):
        print(f"Video position: {position}ms")  # Debug print
        # If we've played the full video, pause it
        if hasattr(self, 'video_duration') and position >= self.video_duration - 100:  # 100ms buffer
            print("Video completed one cycle, pausing")  # Debug print
            self.media_player.pause()
            self.media_player.setPosition(0)  # Reset to beginning
    
    def handle_media_status(self, status):
        print(f"Media status changed: {status}")  # Debug print
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            print("Video ended")  # Debug print
            self.media_player.pause()
            self.media_player.setPosition(0)  # Reset to beginning
    
    def handle_bell_status(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.bell_player.stop()
    
    def handle_access_response(self, response):
        # Cancel any existing timeout timer
        if self.timeout_timer and self.timeout_timer.isActive():
            self.timeout_timer.stop()
        
        # Parse the response
        if response.lower() == "granted":
            self.play_animation()
        else:
            # Show the denial reason
            self.show_denial_reason(response)
    
    def show_denial_reason(self, reason):
        print(f"Access denied: {reason}")  # Debug print
        
        # Set the status label text and style
        self.status_label.setText(f"Access Denied\n{reason}")
        self.status_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: red;
            background-color: black;
            padding: 20px;
            border-radius: 10px;
        """)
        
        # Show the status label
        self.status_label.show()
        
        # Set a timer to return to idle mode after 3 seconds
        self.timeout_timer = QTimer()
        self.timeout_timer.setSingleShot(True)
        self.timeout_timer.timeout.connect(self.show_idle)
        self.timeout_timer.start(3000)  # 3 seconds

    def on_mqtt_connected(self):
        """Callback for when MQTT client connects successfully"""
        print("MQTT client connected and ready")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = BHOUTGate()
    window.show()
    sys.exit(app.exec()) 
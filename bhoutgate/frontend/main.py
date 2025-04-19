import sys
import json
import os
import time
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import Qt, QTimer, QUrl, Signal, QObject
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtGui import QColor, QPalette
import paho.mqtt.client as mqtt

class MQTTClient(QObject):
    message_received = Signal(str)  # Signal to emit when a message is received

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(self.config['mqtt_broker'], self.config['mqtt_port'], 60)
        self.client.loop_start()

    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected to MQTT broker, subscribing to {self.config['mqtt_subscribe_topic']}")
        client.subscribe(self.config['mqtt_subscribe_topic'])

    def on_message(self, client, userdata, msg):
        print(f"Received message on {msg.topic}: {msg.payload.decode()}")
        if msg.topic == self.config['mqtt_subscribe_topic']:
            self.message_received.emit(msg.payload.decode())

    def publish(self, topic, message):
        self.client.publish(topic, message)

class BHOUTGate(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BHOUTGate")
        self.showFullScreen()
        
        # Load configuration
        self.load_config()
        
        # Setup MQTT client
        self.mqtt_client = MQTTClient(self.config)
        self.mqtt_client.message_received.connect(self.handle_access_response)
        
        # Setup UI
        self.setup_ui()
        
        # Start video playback
        self.play_video()
        
        # Initialize timeout timer
        self.timeout_timer = None
    
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
                if 'timeout_seconds' not in self.config:
                    self.config['timeout_seconds'] = 5
                print(f"Loaded configuration: {self.config}")
        except Exception as e:
            print(f"Error loading config: {e}")
            self.config = {
                'mqtt_broker': 'localhost',
                'mqtt_port': 1883,
                'mqtt_publish_topic': 'bhoutgate/scan_code',
                'mqtt_subscribe_topic': 'bhoutgate/access_granted',
                'timeout_seconds': 5,
                'video_path': os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', 'static', 'video.mp4')
            }
    
    def setup_ui(self):
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create video widget
        self.video_widget = QVideoWidget()
        layout.addWidget(self.video_widget)
        
        # Create media player
        self.media_player = QMediaPlayer()
        self.media_player.setVideoOutput(self.video_widget)
        
        # Create status label
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(self.status_label)
        
        # Create scan button
        self.scan_button = QPushButton("Simulate QR Scan")
        self.scan_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 20px;
                font-size: 24px;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.scan_button.clicked.connect(self.simulate_scan)
        layout.addWidget(self.scan_button)
        
        # Hide status label initially
        self.status_label.hide()
    
    def play_video(self):
        video_path = self.config['video_path']
        if os.path.exists(video_path):
            self.media_player.setSource(QUrl.fromLocalFile(video_path))
            self.media_player.play()
            self.media_player.mediaStatusChanged.connect(self.handle_media_status)
        else:
            print(f"Video file not found at: {video_path}")
    
    def handle_media_status(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.media_player.setPosition(0)
            self.media_player.play()
    
    def simulate_scan(self):
        # Cancel any existing timeout timer
        if self.timeout_timer and self.timeout_timer.isActive():
            self.timeout_timer.stop()
        
        # Publish a simulated QR code
        print(f"Publishing to {self.config['mqtt_publish_topic']}")
        self.mqtt_client.publish(self.config['mqtt_publish_topic'], "simulated_qr_code")
        
        # Show waiting state
        self.status_label.setText("Waiting for access response...")
        self.status_label.setStyleSheet("font-size: 24px; font-weight: bold; color: black;")
        self.status_label.show()
        
        # Set timeout timer
        self.timeout_timer = QTimer()
        self.timeout_timer.setSingleShot(True)
        self.timeout_timer.timeout.connect(self.handle_timeout)
        self.timeout_timer.start(self.config['timeout_seconds'] * 1000)
    
    def handle_access_response(self, response):
        # Cancel the timeout timer when receiving a response
        if self.timeout_timer and self.timeout_timer.isActive():
            self.timeout_timer.stop()
        
        if response.lower() == "granted":
            self.show_access_granted()
        else:
            self.show_access_denied(response)
    
    def handle_timeout(self):
        self.show_access_denied("Timeout: No response received")
    
    def show_access_granted(self):
        self.status_label.setText("Access Granted")
        self.status_label.setStyleSheet("font-size: 24px; font-weight: bold; color: green;")
        # Use the class timer for reset
        self.timeout_timer = QTimer()
        self.timeout_timer.setSingleShot(True)
        self.timeout_timer.timeout.connect(self.reset_ui)
        self.timeout_timer.start(3000)  # 3 seconds to show the granted message
    
    def show_access_denied(self, message):
        self.status_label.setText(f"Access Denied: {message}")
        self.status_label.setStyleSheet("font-size: 24px; font-weight: bold; color: red;")
        # Use the class timer for reset
        self.timeout_timer = QTimer()
        self.timeout_timer.setSingleShot(True)
        self.timeout_timer.timeout.connect(self.reset_ui)
        self.timeout_timer.start(3000)  # 3 seconds to show the denied message
    
    def reset_ui(self):
        # Stop any active timer
        if self.timeout_timer and self.timeout_timer.isActive():
            self.timeout_timer.stop()
        self.timeout_timer = None
        
        # Reset UI
        self.status_label.hide()
        self.play_video()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = BHOUTGate()
    window.show()
    sys.exit(app.exec()) 
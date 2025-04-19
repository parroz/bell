import sys
import json
import os
import time
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtGui import QColor, QPalette
import paho.mqtt.client as mqtt

class BHOUTGate(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BHOUTGate")
        self.showFullScreen()
        
        # Load configuration
        self.load_config()
        
        # Setup MQTT client
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.connect(self.config['mqtt_broker'], self.config['mqtt_port'], 60)
        self.mqtt_client.loop_start()
        
        # Setup UI
        self.setup_ui()
        
        # Start video playback
        self.play_video()
    
    def load_config(self):
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'settings.json')
        try:
            with open(config_path, 'r') as f:
                self.config = json.load(f)
        except:
            self.config = {
                'mqtt_broker': 'localhost',
                'mqtt_port': 1883,
                'mqtt_topic': 'bhoutgate/access',
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
    
    def on_connect(self, client, userdata, flags, rc):
        print("Connected to MQTT broker")
        client.subscribe(self.config['mqtt_topic'])
    
    def on_message(self, client, userdata, msg):
        if msg.topic == self.config['mqtt_topic']:
            self.handle_access_response(msg.payload.decode())
    
    def simulate_scan(self):
        # Publish a simulated QR code
        self.mqtt_client.publish(self.config['mqtt_topic'], "simulated_qr_code")
        
        # Show waiting state
        self.status_label.setText("Waiting for access response...")
        self.status_label.setStyleSheet("font-size: 24px; font-weight: bold; color: black;")
        self.status_label.show()
        
        # Set timeout timer
        QTimer.singleShot(self.config['timeout_seconds'] * 1000, self.handle_timeout)
    
    def handle_access_response(self, response):
        if response.lower() == "granted":
            self.show_access_granted()
        else:
            self.show_access_denied(response)
    
    def handle_timeout(self):
        self.show_access_denied("Timeout: No response received")
    
    def show_access_granted(self):
        self.status_label.setText("Access Granted")
        self.status_label.setStyleSheet("font-size: 24px; font-weight: bold; color: green;")
        QTimer.singleShot(3000, self.reset_ui)
    
    def show_access_denied(self, message):
        self.status_label.setText(f"Access Denied: {message}")
        self.status_label.setStyleSheet("font-size: 24px; font-weight: bold; color: red;")
        QTimer.singleShot(3000, self.reset_ui)
    
    def reset_ui(self):
        self.status_label.hide()
        self.play_video()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = BHOUTGate()
    window.show()
    sys.exit(app.exec()) 
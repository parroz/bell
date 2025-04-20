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
                    self.config['mqtt_bell_topic'] = '/bell/ring'
                if 'timeout_seconds' not in self.config:
                    self.config['timeout_seconds'] = 5
                if 'bell_sound_path' not in self.config:
                    self.config['bell_sound_path'] = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', 'static', 'bell.mp3')
                print(f"Loaded configuration: {self.config}")
        except Exception as e:
            print(f"Error loading config: {e}")
            self.config = {
                'mqtt_broker': 'localhost',
                'mqtt_port': 1883,
                'mqtt_publish_topic': 'bhoutgate/scan_code',
                'mqtt_subscribe_topic': 'bhoutgate/access_granted',
                'mqtt_bell_topic': '/bell/ring',
                'timeout_seconds': 5,
                'bell_sound_path': os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', 'static', 'bell.mp3'),
                'video_path': os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', 'static', 'video.mp4')
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
        print(f"Publishing bell ring to {self.config['mqtt_bell_topic']}")  # Debug print
        self.mqtt_client.publish(self.config['mqtt_bell_topic'], "ring")
        
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
        
        # If access is granted, play animation
        if response.lower() == "granted":
            self.play_animation()
    
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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = BHOUTGate()
    window.show()
    sys.exit(app.exec()) 
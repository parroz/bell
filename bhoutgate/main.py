print("Starting BHOUTGate main application...")
print("Loading configuration...")
print("Setting up UI...")
print("Setting up MQTT client...")
print("Initializing media players...")
print("Showing full screen...")
print("Starting in idle mode...")
print("Starting heartbeat timer...")
import sys
import json
import os
import ssl
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QLineEdit, QSizePolicy, QGraphicsView, QGraphicsScene, QGraphicsTextItem, QGraphicsRectItem
from PySide6.QtCore import Qt, QTimer, QUrl, Signal, QObject, QRectF
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QGraphicsVideoItem
from PySide6.QtGui import QPixmap, QColor, QBrush, QPen, QFont, QPainter
import paho.mqtt.client as mqtt

os.environ["GST_VIDEOSINK"] = "glimagesink"

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
        self.video_item = None
        self.status_label = None
        
        # Load configuration
        self.config = self.load_config()
        
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
        
        # Play video once at startup, then go to idle
        QTimer.singleShot(0, self.play_video_once_at_startup)
        
        # Start in idle mode
        self.show_idle()
        
        # Start heartbeat timer
        self.heartbeat_timer = QTimer()
        self.heartbeat_timer.timeout.connect(self.send_heartbeat)
        self.heartbeat_timer.start(self.config['heartbeat']['periodicity_seconds'] * 1000)
    
    def load_config(self):
        try:
            with open('config/config.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return {}
    
    def setup_ui(self):
        self.screen_width = 720
        self.screen_height = 720
        print(f"Forcing screen size: {self.screen_width}x{self.screen_height}")
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create graphics view for video and overlays
        self.graphics_view = QGraphicsView()
        self.graphics_view.setFixedSize(self.screen_width, self.screen_height)
        self.graphics_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.graphics_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.graphics_view.setStyleSheet("background-color: black;")
        main_layout.addWidget(self.graphics_view)
        
        # Create scene
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, self.screen_width, self.screen_height)
        self.graphics_view.setScene(self.scene)
        
        # Create video item
        self.video_item = QGraphicsVideoItem()
        self.video_item.setSize(self.scene.sceneRect().size())
        self.video_item.setZValue(0)  # Video at the bottom
        self.scene.addItem(self.video_item)
        
        # Create background rectangle for text
        self.background_rect = QGraphicsRectItem(0, self.screen_height - 120, self.screen_width, 100)
        self.background_rect.setBrush(QBrush(QColor(0, 0, 0, 200)))
        self.background_rect.setZValue(1)  # Above video
        self.background_rect.hide()
        self.scene.addItem(self.background_rect)
        
        # Create text item for denial message
        self.denial_text = QGraphicsTextItem()
        self.denial_text.setDefaultTextColor(QColor("white"))
        font = QFont()
        font.setPointSize(36)
        font.setBold(True)
        self.denial_text.setFont(font)
        self.denial_text.setZValue(2)  # Above background
        self.denial_text.hide()
        self.scene.addItem(self.denial_text)
        
        print("UI setup complete")
    
    def setup_media(self):
        # Setup video player
        self.media_player = QMediaPlayer()
        self.media_player.setVideoOutput(self.video_item)
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
        if not os.path.isabs(video_path):
            video_path = os.path.abspath(video_path)
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
        
        self.denial_text.hide()
        self.background_rect.hide()
        
        print("Returned to idle mode")
    
    def resizeEvent(self, event):
        print("Window size:", self.size())
        print("Video item size:", self.video_item.size())
        super().resizeEvent(event)
    
    def mousePressEvent(self, event):
        if self.video_item.isVisible() and not self.background_rect.isVisible():
            self.play_animation()
    
    def play_animation(self):
        print("Starting animation")
        
        # Send button press message
        button_press = {"ringing": True}
        import json
        self.mqtt_client.publish(self.config['mqtt']['topics']['button_press'], json.dumps(button_press))
        
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
        print(f"Raw access response: {response}")  # Debug: show full response
        if self.timeout_timer and self.timeout_timer.isActive():
            self.timeout_timer.stop()
        
        try:
            # Parse the response JSON
            import json
            response_data = json.loads(response)
            
            if response_data.get("open", False):
                # Send command to Shelly door control
                shelly_command = {
                    "id": 1,
                    "src": "bhout-mqtt-cli",
                    "method": "Switch.Set",
                    "params": {
                        "id": 0,
                        "on": True
                    }
                }
                self.mqtt_client.publish("doorshelly/rpc", json.dumps(shelly_command))
                print("Sent door open command to Shelly")
                
                self.play_animation()
            else:
                # Get the reason if provided
                reason = response_data.get("reason", "")
                if reason:
                    print(f"Access denied: {reason}")
                    self.show_denial_reason(reason)
                else:
                    print("Access denied (no reason in response)")
                    self.show_denial_reason("No reason provided by backend")
        except json.JSONDecodeError as e:
            print(f"Error parsing response: {e}")
            self.show_denial_reason(f"Invalid response format: {response}")
        except Exception as e:
            print(f"Error handling response: {e}")
            self.show_denial_reason(f"Error processing response: {e}")
    
    def show_denial_reason(self, reason):
        print(f"Access denied: {reason}")
        
        if reason:
            text = f"Access Denied: {reason}"
        else:
            text = "Access Denied"
        
        # Update text
        self.denial_text.setPlainText(text)
        
        # Center the text
        text_width = self.denial_text.boundingRect().width()
        text_height = self.denial_text.boundingRect().height()
        x = (self.screen_width - text_width) / 2
        y = self.screen_height - 120 + (100 - text_height) / 2
        self.denial_text.setPos(x, y)
        
        # Show overlay
        self.background_rect.show()
        self.denial_text.show()
        
        # Force updates
        self.scene.update()
        
        # Add debug prints
        print(f"Denial text: {text}")
        print(f"Text position: ({x}, {y})")
        print(f"Text is visible: {self.denial_text.isVisible()}")
        print(f"Background is visible: {self.background_rect.isVisible()}")
        
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

    def send_heartbeat(self):
        self.mqtt_client.publish("bhout/doorbell/heartbeat", "Heartbeat message")

    def play_video_once_at_startup(self):
        print("Playing video once at startup")
        self.media_player.setPosition(0)
        self.media_player.play()
        # When video finishes, go to idle
        self.media_player.mediaStatusChanged.connect(self._on_startup_video_status)

    def _on_startup_video_status(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            print("Startup video finished, returning to idle mode")
            self.media_player.mediaStatusChanged.disconnect(self._on_startup_video_status)
            self.show_idle()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = BHOUTGate()
    window.show()
    sys.exit(app.exec()) 
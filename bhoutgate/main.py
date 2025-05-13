import sys
import os
import json
import time
from datetime import datetime
import paho.mqtt.client as mqtt
from dotenv import load_dotenv
import tkinter as tk
from tkinter import ttk, scrolledtext
from tkinter import messagebox

# Load environment variables
load_dotenv()

# MQTT Configuration
MQTT_BROKER = os.getenv('MQTT_BROKER', 'localhost')
MQTT_PORT = int(os.getenv('MQTT_PORT', '1883'))
MQTT_USERNAME = os.getenv('MQTT_USERNAME', '')
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD', '')
MQTT_TOPIC = os.getenv('MQTT_TOPIC', 'bhout/doorbell/event/open-door')

# Load configuration
def load_config():
    try:
        with open('config/config.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}

config = load_config()

class DoorbellApp:
    def __init__(self, root):
        self.root = root
        self.root.title("BHOUT Gate Control")
        self.root.geometry("800x600")
        
        # Initialize MQTT client
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        
        # Connect to MQTT broker
        if MQTT_USERNAME and MQTT_PASSWORD:
            self.mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        
        try:
            self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.mqtt_client.loop_start()
        except Exception as e:
            messagebox.showerror("Connection Error", 
                               f"Failed to connect to MQTT broker: {str(e)}")
        
        # Create main frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Status: Disconnected")
        self.status_label.grid(row=0, column=0, columnspan=2, pady=5)
        
        # Log display
        self.log_display = scrolledtext.ScrolledText(main_frame, height=20)
        self.log_display.grid(row=1, column=0, columnspan=2, pady=5, sticky=(tk.W, tk.E))
        
        # Control buttons
        self.open_button = ttk.Button(main_frame, text="Open Door", command=self.open_door)
        self.open_button.grid(row=2, column=0, pady=5, padx=5)
        
        self.close_button = ttk.Button(main_frame, text="Close Door", command=self.close_door)
        self.close_button.grid(row=2, column=1, pady=5, padx=5)
        
        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Set up status update
        self.update_status()
        
        self.log("Application started")
    
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.status_label.config(text="Status: Connected")
            self.log("Connected to MQTT broker")
            # Subscribe to the doorbell event topic
            client.subscribe(MQTT_TOPIC)
        else:
            self.status_label.config(text=f"Status: Connection failed (code {rc})")
            self.log(f"Failed to connect to MQTT broker (code {rc})")
    
    def on_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode()
            self.log(f"Received message on {msg.topic}: {payload}")
            
            # Handle the doorbell event
            if msg.topic == MQTT_TOPIC:
                self.handle_doorbell_event(payload)
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
        
        # Start in idle mode
        self.show_idle()
    
    def load_config(self):
        try:
            with open('config/config.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return {}
    
    def open_door(self):
        try:
            # Publish open door command
            self.mqtt_client.publish(MQTT_TOPIC, json.dumps({
                'command': 'open',
                'timestamp': datetime.now().isoformat()
            }))
            self.log("Open door command sent")
        except Exception as e:
            self.log(f"Error sending open door command: {str(e)}")
    
    def close_door(self):
        try:
            # Publish close door command
            self.mqtt_client.publish(MQTT_TOPIC, json.dumps({
                'command': 'close',
                'timestamp': datetime.now().isoformat()
            }))
            self.log("Close door command sent")
        except Exception as e:
            self.log(f"Error sending close door command: {str(e)}")
    
    def update_status(self):
        if self.mqtt_client.is_connected():
            self.status_label.config(text="Status: Connected")
        else:
            self.status_label.config(text="Status: Disconnected")
        self.root.after(1000, self.update_status)  # Update every second
    
    def log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_display.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_display.see(tk.END)  # Scroll to the end
    
    def on_closing(self):
        self.mqtt_client.loop_stop()
        self.mqtt_client.disconnect()
        self.root.destroy()

if __name__ == '__main__':
    root = tk.Tk()
    app = DoorbellApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop() 
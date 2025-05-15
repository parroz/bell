import sys
import json
import os
import ssl
import paho.mqtt.client as mqtt
import time
import subprocess

class MQTTClient:
    def __init__(self, config):
        self.config = config
        self.client = None
        self.is_connected = False
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
            ca_cert = self.config['mqtt']['ca_cert']
            client_cert = self.config['mqtt']['client_cert']
            client_key = self.config['mqtt']['client_key']
            
            # Print current working directory and list its contents
            print(f"\nCurrent working directory: {os.getcwd()}")
            print("\nContents of current directory:")
            subprocess.run(['ls', '-la'], check=True)
            
            # Print config/static directory contents
            print("\nContents of config/static directory:")
            subprocess.run(['ls', '-la', 'config/static'], check=True)
            
            # Check if certificate files exist
            certs_exist = True
            for cert_file in [ca_cert, client_cert, client_key]:
                abs_path = os.path.abspath(cert_file)
                print(f"\nChecking certificate file: {cert_file}")
                print(f"Absolute path: {abs_path}")
                if not os.path.exists(cert_file):
                    print(f"WARNING: Certificate file does not exist: {cert_file}")
                    certs_exist = False
                else:
                    print(f"Certificate file exists: {cert_file}")
                    print(f"File permissions: {oct(os.stat(cert_file).st_mode)[-3:]}")
            
            if certs_exist:
                print("Using full TLS configuration with client certificates")
                self.client.tls_set(
                    ca_certs=ca_cert,
                    certfile=client_cert,
                    keyfile=client_key,
                    cert_reqs=ssl.CERT_REQUIRED,
                    tls_version=ssl.PROTOCOL_TLS,
                    ciphers=None
                )
                self.client.tls_insecure_set(False)
            else:
                print("WARNING: Certificate files not found. The broker may require client certificates.")
                print("Attempting to connect with basic TLS configuration...")
                self.client.tls_set(
                    ca_certs=None,
                    certfile=None,
                    keyfile=None,
                    cert_reqs=ssl.CERT_NONE,
                    tls_version=ssl.PROTOCOL_TLS,
                    ciphers=None
                )
                self.client.tls_insecure_set(True)
            
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
            
            # Add connection retry logic
            max_retries = 3
            retry_count = 0
            while retry_count < max_retries:
                try:
                    self.client.connect(broker, port, 60)
                    self.client.loop_start()
                    print("MQTT client loop started")
                    break
                except ssl.SSLError as e:
                    if "certificate required" in str(e).lower():
                        print("ERROR: Broker requires client certificates. Please ensure all certificate files are present.")
                        print("Required files:")
                        print(f"- CA Certificate: {ca_cert}")
                        print(f"- Client Certificate: {client_cert}")
                        print(f"- Client Key: {client_key}")
                        break
                    else:
                        retry_count += 1
                        if retry_count < max_retries:
                            print(f"SSL Error: {e}")
                            print(f"Retrying connection ({retry_count}/{max_retries})...")
                            time.sleep(2)
                        else:
                            print(f"Failed to connect after {max_retries} attempts")
                            raise
                except Exception as e:
                    retry_count += 1
                    if retry_count < max_retries:
                        print(f"Connection error: {e}")
                        print(f"Retrying connection ({retry_count}/{max_retries})...")
                        time.sleep(2)
                    else:
                        print(f"Failed to connect after {max_retries} attempts")
                        raise
        except Exception as e:
            print(f"Error connecting to MQTT broker: {e}")
            raise

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT broker successfully")
            self.is_connected = True
            subscribe_topic = self.config['mqtt']['topics']['subscribe']
            print(f"Subscribing to topic: {subscribe_topic}")
            client.subscribe(subscribe_topic)
        else:
            print(f"Failed to connect to MQTT broker, return code: {rc}")
            self.is_connected = False

    def on_publish(self, client, userdata, mid):
        print(f"Message published successfully (mid: {mid})")

    def on_disconnect(self, client, userdata, rc):
        print("Disconnected from MQTT broker")
        self.is_connected = False

    def on_message(self, client, userdata, msg):
        print(f"Received message on {msg.topic}: {msg.payload.decode()}")

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
        except Exception as e:
            print(f"Error publishing message: {e}")

def load_config():
    try:
        with open('config/config.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}

def main():
    print("Starting BHOUTGate test application...")
    config = load_config()
    if not config:
        print("Failed to load configuration")
        return

    mqtt_client = MQTTClient(config)
    
    # Keep the script running and publish a heartbeat message every 30 seconds
    try:
        while True:
            mqtt_client.publish("bhout/doorbell/heartbeat", "Heartbeat message")
            time.sleep(30)
    except KeyboardInterrupt:
        print("\nShutting down...")
        if mqtt_client.client:
            mqtt_client.client.disconnect()
            mqtt_client.client.loop_stop()

if __name__ == "__main__":
    main() 
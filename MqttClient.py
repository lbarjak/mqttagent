import paho.mqtt.client as mqtt
import threading
import time
import json


class MqttClient:
    def __init__(self, message="", topics=None, on_message=None, config=None):
        print("init topics:", topics)
        if topics is None:
            topics = ["zigbee2mqtt/hőmérő_sz1"]  # Default topic if none provided

        # Load config
        if config is None:
            with open("config.json", "r") as file:
                config = json.load(file)
        
        self.config = config
        broker_ip = config["mqtt"]["broker"]
        port = config["mqtt"]["port"]
        keepalive = config["mqtt"]["keepalive"]
        self.missing_data_timeout = config["mqtt"]["missing_data_timeout"]

        self.topics = topics  # Store topics for resubscription after reconnect
        self.client = mqtt.Client()
        self.message = message
        self.on_message = on_message  # Callback for incoming messages
        
        # Set callbacks BEFORE connecting
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message_received
        self.client.on_disconnect = self.on_disconnect
        
        self.client.connect(broker_ip, port, keepalive=keepalive)

        # NOTE: Subscriptions are handled in on_connect callback (see line ~49)
        # This ensures subscriptions are renewed after reconnects automatically
        
        # NOTE: loop_start() removed - loop_forever() is called in main.py instead
        # self.client.loop_start()  # Start the loop in a non-blocking way

        self.data_timer = None  # Időzítő inicializálása

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected successfully")
            # Resubscribe to all topics after reconnect to prevent subscription loss
            for topic in self.topics:
                self.subscribe(topic)
                print(f"Subscribed to: {topic}")
            print("-" * 54)
            self.reset_data_timer()  # Start the timer
        else:
            print(f"Connection failed with code {rc}")
            print("-" * 54)

    def subscribe(self, topic):
        self.client.subscribe(topic)

    def publish_message(self, topic, message, qos=2, retain = True):  # Use QoS 0 for testing
        self.client.publish(topic, message, qos=qos, retain=retain)
        # print(f"Message published: {message}")

    def on_message_received(self, client, userdata, msg):
        if self.on_message:
            try:
                payload = msg.payload.decode('utf-8')
                self.on_message(msg.topic, payload)
            except UnicodeDecodeError as e:
                print(f"Error: Failed to decode message from {msg.topic}: {e}")
                return
            except Exception as e:
                print(f"Error in message callback for {msg.topic}: {e}")
                return
        self.reset_data_timer()  # Üzenet érkezett, reseteli az időzítőt

    def on_disconnect(self, client, userdata, rc):
        print("Disconnected from broker")
        if rc != 0:
            print(f"Unexpected disconnection (code {rc}). Will auto-reconnect...")
        # NOTE: Do NOT manually call reconnect() here - loop_forever() handles it automatically
        # Manually calling reconnect() in the callback blocks the network thread and causes issues

    def reset_data_timer(self):
        if self.data_timer is not None:
            self.data_timer.cancel()  # Állítsd le a korábbi időzítőt
        self.data_timer = threading.Timer(
            self.missing_data_timeout, self.on_missing_data
        )
        self.data_timer.start()  # Indítsd el az új időzítőt

    def on_missing_data(self):
        print(f"Warning: No data received for {self.missing_data_timeout} seconds.")
        print("-" * 54)
        self.reset_data_timer()  # Újraindítja az időzítőt

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()

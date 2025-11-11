import paho.mqtt.client as mqtt
import threading
import time


class MqttClient:
    def __init__(self, message="", topics=None, on_message=None):
        print("init topics:", topics)
        if topics is None:
            topics = ["zigbee2mqtt/hőmérő_sz1"]  # Default topic if none provided

        # Read the IP address from ip.txt file
        with open("ip.txt", "r") as file:
            ip_address = (
                file.readline().strip()
            )  # Read the first line and strip whitespace

        self.topics = topics  # Store topics for resubscription after reconnect
        self.client = mqtt.Client()
        self.client.on_message = self.on_message_received
        self.client.connect(
            ip_address, 1883, keepalive=60
        )  # Use the IP address read from the file
        self.client.on_connect = self.on_connect
        self.message = message
        self.on_message = on_message  # Callback for incoming messages

        # Subscribe to all topics in the provided list
        for topic in self.topics:
            self.subscribe(topic)

        self.client.loop_start()  # Start the loop in a non-blocking way

        self.missing_data_timeout = 240  # Idő (másodpercekben) a figyelmeztetéshez
        self.data_timer = None  # Időzítő inicializálása
        self.client.on_disconnect = self.on_disconnect  # Kapcsolat megszakadás kezelése

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
            self.on_message(
                msg.topic, msg.payload.decode()
            )  # Call the callback with the message
        self.reset_data_timer()  # Üzenet érkezett, reseteli az időzítőt

    def on_disconnect(self, client, userdata, rc):
        print("Disconnected from broker")
        if rc != 0:
            print("Unexpected disconnection. Attempting to reconnect...")

        max_retries = 5  # Maximális próbálkozások száma
        for attempt in range(max_retries):
            try:
                time.sleep(5)  # Várj 5 másodpercet az újracsatlakozás előtt
                self.client.reconnect()  # Újra próbálkozás a kapcsolattal
                print("Reconnected successfully")
                break  # Sikeres újracsatlakozás esetén kilép a ciklusból
            except Exception as e:
                print(
                    f"Reconnect failed: {e}. Retrying ({attempt + 1}/{max_retries})..."
                )
        else:
            print("Max retries reached. Could not reconnect.")

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

import paho.mqtt.client as mqtt


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

        self.client = mqtt.Client()
        self.client.on_message = self.on_message_received
        self.client.connect(ip_address, 1883)  # Use the IP address read from the file
        self.message = message
        self.on_message = on_message  # Callback for incoming messages

        # Subscribe to all topics in the provided list
        for topic in topics:
            self.subscribe(topic)

        self.client.loop_start()  # Start the loop in a non-blocking way

    def subscribe(self, topic):
        self.client.subscribe(topic)

    def publish_message(self, topic, message, qos=2):  # Use QoS 0 for testing
        self.client.publish(topic, message, qos=qos)
        # print(f"Message published: {message}")

    def on_message_received(self, client, userdata, msg):
        if self.on_message:
            self.on_message(
                msg.topic, msg.payload.decode()
            )  # Call the callback with the message

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()

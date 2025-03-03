from MqttClient import MqttClient
from Averages import TempsFile
from datetime import datetime
import time
import json
from Dev import Dev, devs


def load_devices():
    try:
        with open("devices.txt", "r") as file:
            devices = file.read().split("\n")
        return devices
    except FileNotFoundError:
        print("Error: devices.txt file not found.")
        return []
    except Exception as e:
        print(f"Error reading devices.txt: {e}")
        return []


devices = load_devices()
topics = []
for device in devices:
    if device:  # Check if device is not an empty string
        topics.append(f"zigbee2mqtt/{device}")
        devs[device] = Dev(device)
for dev in devs:
    print(f"devs[{dev}].device:", devs[dev].device)

temps_file = TempsFile()


def handle_message(topic, message):
    from_device = topic.split("/")[1]
    print(f"from: {from_device}")
    # print(f"Message content: {message}")
    print(datetime.now())
    try:
        json_message = json.loads(message)
        temp = json_message["temperature"]
        print(f"temperature: {temp}")
        hum = json_message["humidity"]
        print(f"humidity: {hum}")
        batt = json_message["battery"]
        print(f"battery: {batt}")
        devs[from_device].temperature = temp
        devs[from_device].humidity = hum
        devs[from_device].battery = batt
        temps_file.add_temp(from_device, temp)
        temps_file.save_temps()
        devs[from_device].average = temps_file.get_average(from_device)
        print(f"Average temperature: {temps_file.get_average(from_device)}")
        mqtt_client.publish_message(
            "average/" + from_device, temps_file.get_average(from_device)
        )
        print("-" * 54)
    except json.JSONDecodeError:
        print("Error: Failed to decode JSON message.")
    except KeyError as e:
        print(f"Error: Missing key in JSON message: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


mqtt_client = MqttClient(
    topics=topics, on_message=handle_message
)  # Pass the callback function

mqtt_client.publish_message("alert/mqttagent", "mqttagent started")

# Main loop to keep the script running
try:
    while True:
        time.sleep(1)  # Sleep to prevent high CPU usage
except KeyboardInterrupt:
    print("Exiting...")

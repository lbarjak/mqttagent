from MqttClient import MqttClient
from Averages import TempsFile
from datetime import datetime
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


def handle_message(topic, message):
    from_device = topic.split("/")[1]
    print(f"from: {from_device}")
    print(datetime.now())
    try:
        json_message = json.loads(message)
        temp = json_message["temperature"]
        hum = json_message["humidity"]
        batt = json_message["battery"]

        # Update device data
        devs[from_device].temperature = temp
        devs[from_device].humidity = hum
        devs[from_device].battery = batt

        # Log temperature and save to file
        temps_file.add_temp(from_device, temp)
        temps_file.save_temps()

        # Calculate and publish average temperature
        average_temp = temps_file.get_average(from_device)
        devs[from_device].average = average_temp

        # mqtt_client.publish_message("average/" + from_device, average_temp)

        print(f"temperature: {temp}, humidity: {hum}, battery: {batt}")
        print(f"Average temperature: {average_temp}")
        print("-" * 54)
    except json.JSONDecodeError:
        print("Error: Failed to decode JSON message.")
    except KeyError as e:
        print(f"Error: Missing key in JSON message: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


# Load devices and initialize MQTT client
devices = load_devices()
topics = [f"zigbee2mqtt/{device}" for device in devices if device]
devs.update({device: Dev(device) for device in devices if device})
for dev in devs:
    print(f"devs[{dev}].device:", devs[dev].device)
temps_file = TempsFile()

mqtt_client = MqttClient(
    topics=topics, on_message=handle_message
)  # Pass the callback function

mqtt_client.publish_message("alert/mqttagent", "mqttagent started")

try:
    mqtt_client.client.loop_forever()
except KeyboardInterrupt:
    print("Exiting...")

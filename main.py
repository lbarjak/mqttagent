from MqttClient import MqttClient
from Averages import TempsFile
from datetime import datetime
import json
from Dev import Dev, devs


def load_config():
    """Load configuration from config.json."""
    try:
        with open("config.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        print("Error: config.json file not found.")
        return None
    except Exception as e:
        print(f"Error reading config.json: {e}")
        return None


def load_devices(config):
    """Load devices from config.json."""
    if config and "devices" in config:
        return config["devices"]
    
    print("Error: 'devices' key not found in config.json")
    return []


def handle_message(topic, message):
    try:
        from_device = topic.split("/")[1]
        print(f"from: {from_device}")
        print(datetime.now())
        
        json_message = json.loads(message)
        temp = json_message["temperature"]
        hum = json_message["humidity"]
        batt = json_message["battery"]

        # Update device data
        if from_device not in devs:
            print(f"Warning: Unknown device '{from_device}' - ignoring message")
            return
            
        devs[from_device].temperature = temp
        devs[from_device].humidity = hum
        devs[from_device].battery = batt

        # Log temperature (will be saved by background thread)
        temps_file.add_temp(from_device, temp)

        # Calculate and publish average temperature
        average_temp = temps_file.get_average(from_device)
        devs[from_device].average = average_temp

        # mqtt_client.publish_message("average/" + from_device, average_temp)

        print(f"temperature: {temp}, humidity: {hum}, battery: {batt}")
        print(f"Average temperature: {average_temp}")
        print("-" * 54)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to decode JSON message from {topic}: {e}")
        print("-" * 54)
    except KeyError as e:
        print(f"Error: Missing key in JSON message from {topic}: {e}")
        print("-" * 54)
    except IndexError as e:
        print(f"Error: Invalid topic format '{topic}': {e}")
        print("-" * 54)
    except Exception as e:
        print(f"Unexpected error handling message from {topic}: {e}")
        print("-" * 54)


# Load config and initialize
config = load_config()
if not config:
    print("Fatal: Could not load config.json. Exiting.")
    exit(1)

devices = load_devices(config)
topics_prefix = config.get("topics_prefix", "zigbee2mqtt")
topics = [f"{topics_prefix}/{device}" for device in devices if device]
devs.update({device: Dev(device) for device in devices if device})
for dev in devs:
    print(f"devs[{dev}].device:", devs[dev].device)

temps_file = TempsFile(config=config)

mqtt_client = MqttClient(
    topics=topics, on_message=handle_message, config=config
)  # Pass the callback function

mqtt_client.publish_message("alert/mqttagent", "mqttagent started")

try:
    mqtt_client.client.loop_forever()
except KeyboardInterrupt:
    print("\nExiting...")
    mqtt_client.publish_message("alert/mqttagent", "mqttagent stopped")
    mqtt_client.disconnect()
    temps_file.save_temps()  # Ensure all data is saved before exit
    print("Cleanup complete.")

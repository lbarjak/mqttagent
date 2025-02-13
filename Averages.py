import os
from datetime import datetime, timedelta

TEMPS_FILE = "temps.txt"


class TempsFile:
    def __init__(self):
        self.temps = {}  # The stucture: {device: {timestamp: temperature}}
        self.load_temps()

    def load_temps(self):
        if os.path.exists(TEMPS_FILE):
            with open(TEMPS_FILE, "r") as file:
                for line in file:
                    device, *temp_list = line.strip().split(",")
                    self.temps[device] = {}
                    for entry in temp_list:
                        timestamp, temperature = entry.split(" ")
                        self.temps[device][timestamp] = float(temperature)

    def save_temps(self):
        with open(TEMPS_FILE, "w") as file:
            for device, timestamps in self.temps.items():
                temp_entries = [
                    f"{timestamp} {temp}" for timestamp, temp in timestamps.items()
                ]
                file.write(f"{device},{','.join(temp_entries)}\n")

    def add_temp(self, device, temp):
        timestamp = datetime.now().isoformat()  # Current timestamp
        if device not in self.temps:
            self.temps[device] = {}

        # Adding temperature to timestamp key
        self.temps[device][timestamp] = temp
        self.save_temps()

    def get_average(self, device):
        if device not in self.temps:
            return 0.0  # Return 0.0 if no data is available

        device_temps = self.temps[device].values()  # Values of the timestamp keys

        if device_temps:
            average = round((sum(device_temps) / len(device_temps)), 2)
            return average
        return None

    def filter_last_24_hours(self, device):
        """Filter data from the last 24 hours."""
        if device not in self.temps:
            print(f"No data for device '{device}'.")
            return {}

        now = datetime.now()  # Current time
        yesterday = now - timedelta(hours=24)  # # 24 hours ago

        # Store filtered data
        filtered_temps = {}
        for timestamp, temperature in self.temps[device].items():
            # Check if the timestamp is within the last 24 hours
            if datetime.fromisoformat(timestamp) >= yesterday:
                filtered_temps[timestamp] = temperature

        return filtered_temps

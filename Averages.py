import os
from datetime import datetime, timedelta

TEMPS_FILE = "temps.txt"


class TempsFile:
    def __init__(self):
        self.temps = {}
        self.load_temps()

    def load_temps(self):
        """Load temperature readings from the file."""
        if os.path.exists(TEMPS_FILE):
            with open(TEMPS_FILE, "r") as file:
                for line in file:
                    device, *temp_list = line.strip().split(",")
                    self.temps[device] = {}
                    for entry in temp_list:
                        timestamp, temperature = entry.split(" ")
                        self.temps[device][timestamp] = float(temperature)

    def save_temps(self):
        """Save only the last 24 hours' temperature readings to the file."""
        with open(TEMPS_FILE, "w") as file:
            for device, timestamps in self.temps.items():
                # Szűrjük ki a 24 óránál régebbi adatokat
                current_time = datetime.now()
                filtered_timestamps = {
                    timestamp: temperature
                    for timestamp, temperature in timestamps.items()
                    if datetime.fromisoformat(timestamp)
                    >= current_time - timedelta(hours=24)
                }

                if filtered_timestamps:  # Csak akkor írunk, ha van érvényes adat
                    temp_entries = [
                        f"{timestamp} {temp}"
                        for timestamp, temp in filtered_timestamps.items()
                    ]
                    file.write(f"{device},{','.join(temp_entries)}\n")

    def add_temp(self, device, temp):
        """Add a new temperature reading for a device."""
        timestamp = datetime.now().isoformat()
        if device not in self.temps:
            self.temps[device] = {}
        self.temps[device][timestamp] = temp
        self.save_temps()

    def filter_last_24_hours(self, device):
        """Filter data from the last 24 hours."""
        if device not in self.temps:
            print(f"No data for device '{device}'.")
            return {}

        now = datetime.now()  # Current time
        yesterday = now - timedelta(hours=24)  # 24 hours ago

        # Store filtered data
        filtered_temps = {}
        for timestamp, temperature in self.temps[device].items():
            # Check if the timestamp is within the last 24 hours
            if datetime.fromisoformat(timestamp) >= yesterday:
                filtered_temps[timestamp] = temperature

        return filtered_temps

    def get_average(self, device):
        """Calculate the average temperature for the last 24 hours."""
        if device not in self.temps:
            return 0.0

        filtered_temps = self.filter_last_24_hours(device)
        device_temps = filtered_temps.values()

        if device_temps:
            average = round((sum(device_temps) / len(device_temps)), 2)
            return average
        return None

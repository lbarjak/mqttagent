import os
import threading
from datetime import datetime, timedelta

TEMPS_FILE = "temps.txt"


class TempsFile:
    def __init__(self):
        self.lock = threading.Lock()  # Thread-safety for MQTT callbacks
        self.temps = {}  # Structure: {device: {timestamp: temperature}}
        self.load_temps()

    def load_temps(self):
        """Load temperature readings from the file."""
        with self.lock:
            if os.path.exists(TEMPS_FILE):
                with open(TEMPS_FILE, "r") as file:
                    for line in file:
                        parts = line.strip().split(",")
                        if not parts:
                            continue
                        device = parts[0]
                        temp_list = parts[1:]
                        self.temps[device] = {}
                        for entry in temp_list:
                            entry = entry.strip()
                            if not entry:
                                continue
                            try:
                                timestamp, temperature = entry.rsplit(" ", 1)
                                self.temps[device][timestamp] = float(temperature)
                            except (ValueError, IndexError) as e:
                                print(f"Skipping malformed entry '{entry}': {e}")
                                continue

    def save_temps(self):
        """Save only the last 24 hours' temperature readings to the file."""
        with self.lock:
            current_time = datetime.now()
            cutoff = current_time - timedelta(hours=24)
            
            with open(TEMPS_FILE, "w") as file:
                for device, timestamps in self.temps.items():
                    # Filter out data older than 24 hours
                    filtered_timestamps = {
                        timestamp: temperature
                        for timestamp, temperature in timestamps.items()
                        if datetime.fromisoformat(timestamp) >= cutoff
                    }

                    if filtered_timestamps:  # Only write if there is valid data
                        temp_entries = [
                            f"{timestamp} {temp}"
                            for timestamp, temp in sorted(filtered_timestamps.items())
                        ]
                        file.write(f"{device},{','.join(temp_entries)}\n")
            
            # Clean up old data from memory to prevent memory leak
            for device in list(self.temps.keys()):
                self.temps[device] = {
                    ts: temp for ts, temp in self.temps[device].items()
                    if datetime.fromisoformat(ts) >= cutoff
                }
                # Remove device entry if no data left
                if not self.temps[device]:
                    del self.temps[device]

    def add_temp(self, device, temp):
        """Add a new temperature reading for a device."""
        with self.lock:
            timestamp = datetime.now().isoformat()
            if device not in self.temps:
                self.temps[device] = {}
            self.temps[device][timestamp] = temp
        # Save outside the critical section (save_temps has its own lock)
        self.save_temps()

    def filter_last_24_hours(self, device):
        """Filter data from the last 24 hours."""
        with self.lock:
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
            return None  # Consistent: None if no data

        filtered_temps = self.filter_last_24_hours(device)
        device_temps = filtered_temps.values()

        if device_temps:
            average = round((sum(device_temps) / len(device_temps)), 2)
            return average
        return None

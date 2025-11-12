import os
import threading
import json
import time
from datetime import datetime, timedelta


class TempsFile:
    def __init__(self, config=None):
        # Load config
        if config is None:
            with open("config.json", "r") as file:
                config = json.load(file)
        
        self.config = config
        self.temps_file = config["storage"]["temps_file"]
        self.retention_hours = config["storage"]["retention_hours"]
        self.write_interval = config["storage"]["write_interval"]
        
        self.lock = threading.Lock()  # Thread-safety for MQTT callbacks
        self.temps = {}  # Structure: {device: {timestamp: temperature}}
        self.dirty = False  # Flag to track if data needs saving
        self.last_write_time = time.time()
        
        self.load_temps()
        
        # Start background writer thread for debounced writes
        self.writer_thread = threading.Thread(target=self._background_writer, daemon=True)
        self.writer_thread.start()

    def load_temps(self):
        """Load temperature readings from the file."""
        with self.lock:
            if os.path.exists(self.temps_file):
                with open(self.temps_file, "r") as file:
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

    def _background_writer(self):
        """Background thread that writes to file periodically."""
        while True:
            time.sleep(self.write_interval)
            if self.dirty:
                self._do_save()
    
    def _do_save(self):
        """Internal method to actually save to file."""
        with self.lock:
            current_time = datetime.now()
            cutoff = current_time - timedelta(hours=self.retention_hours)
            
            with open(self.temps_file, "w") as file:
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
            
            self.dirty = False
            self.last_write_time = time.time()
    
    def save_temps(self):
        """Mark data as dirty and save immediately (for compatibility)."""
        self.dirty = True
        self._do_save()

    def add_temp(self, device, temp):
        """Add a new temperature reading for a device."""
        with self.lock:
            timestamp = datetime.now().isoformat()
            if device not in self.temps:
                self.temps[device] = {}
            self.temps[device][timestamp] = temp
            self.dirty = True  # Mark for eventual save by background thread

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
        """Calculate the average temperature for the retention period."""
        if device not in self.temps:
            return None  # Consistent: None if no data

        filtered_temps = self.filter_last_24_hours(device)
        device_temps = list(filtered_temps.values())

        if device_temps:
            average = round((sum(device_temps) / len(device_temps)), 2)
            return average
        return None

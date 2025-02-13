class Dev:
    def __init__(self, device):
        self.temperature = 0.0
        self.humidity = 0.0
        self.device = device
        self.battery = 0.0
        self.average = 0.0


# Dictionary to store device instances
devs = {}

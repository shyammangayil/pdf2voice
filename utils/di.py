class ServiceContainer:
    def __init__(self):
        self._services = {}

    def register(self, interface, instance):
        self._services[interface] = instance

    def resolve(self, interface):
        if interface not in self._services:
            raise ValueError(f"Service {interface} not registered")
        return self._services[interface]
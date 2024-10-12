class UnregisteredInterfaceError(Exception):
    def __init__(self, interface: type):
        super().__init__(f"Interface {interface} not registered.")

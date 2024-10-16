class UnregisteredInterfaceError(Exception):
    def __init__(self, interface: type):
        super().__init__(f"Interface {interface} not registered.")


class ContainerNotCreatedError(Exception):
    def __init__(self):
        super().__init__(
            "Container not created. Consider calling `Container.create()`."
        )


class ContainerAlreadyCreatedError(Exception):
    def __init__(self):
        super().__init__("Container already created.")


class ResolverError(Exception):
    def __init__(self, interface: type):
        super().__init__(f"Resolver for interface {interface} failed.")

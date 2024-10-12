from dipy.exception import UnregisteredInterfaceError
from dipy.providers.provider import Provider


class TransientProvider(Provider):
    def __init__(self) -> None:
        self._interface_to_concrete: dict[type, type] = {}

    def get[T](self, interface: type[T]) -> T:
        if interface not in self._interface_to_concrete:
            raise UnregisteredInterfaceError(interface)

        return self._interface_to_concrete[interface]()

    def register[T](self, interface: type[T], concrete: type[T]) -> None:
        self._interface_to_concrete[interface] = concrete

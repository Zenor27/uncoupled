from dataclasses import dataclass
from typing import Any, cast
from dipy.exception import UnregisteredInterfaceError
from dipy.providers.provider import Provider


@dataclass(kw_only=True, slots=True)
class Singleton[I]:
    type: type[I]
    instance: I | None = None


class SingletonProvider(Provider):
    def __init__(self) -> None:
        self._interface_to_concrete: dict[type, Singleton[Any]] = {}

    def get[T](self, interface: type[T]) -> T:
        if interface not in self._interface_to_concrete:
            raise UnregisteredInterfaceError(interface)

        singleton = self._interface_to_concrete[interface]
        if singleton.instance is None:
            singleton.instance = singleton.type()
        return cast(T, singleton.instance)

    def register[T](self, interface: type[T], concrete: type[T]) -> None:
        self._interface_to_concrete[interface] = Singleton(type=concrete)

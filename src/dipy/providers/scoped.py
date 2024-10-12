from collections.abc import Callable, Hashable
from dataclasses import dataclass
from typing import Any, cast

from dipy.exception import UnregisteredInterfaceError
from dipy.providers.provider import Provider


@dataclass(kw_only=True, slots=True)
class Scoped[I]:
    type: type[I]
    current_scope: Hashable | None = None
    current_instance: I | None = None


class ScopedProvider(Provider):
    def __init__(self, get_scope: Callable[[], Hashable]) -> None:
        self._get_scope = get_scope
        self._interface_to_concrete: dict[type, Scoped[Any]] = {}

    def get[T](self, interface: type[T]) -> T:
        if interface not in self._interface_to_concrete:
            raise UnregisteredInterfaceError(interface)

        scoped = self._interface_to_concrete[interface]
        current_scope = self._get_scope()
        if scoped.current_scope != current_scope:
            scoped.current_scope = current_scope
            scoped.current_instance = scoped.type()
        return cast(T, scoped.current_instance)

    def register[T](self, interface: type[T], concrete: type[T]) -> None:
        self._interface_to_concrete[interface] = Scoped(type=concrete)

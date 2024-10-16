from collections import defaultdict
from dataclasses import dataclass
from logging import Logger
from typing import Any, cast
from dipy.exception import UnregisteredInterfaceError
from dipy.providers.provider import Provider, Registered, Resolver, Marker


@dataclass(kw_only=True, slots=True)
class Singleton[I]:
    instance: I | None = None


class SingletonProvider(Provider):
    def __init__(self, *, logger: Logger) -> None:
        self._interface_to_concretes: dict[type, list[Registered[Any]]] = defaultdict(
            list
        )
        self._registered_to_singleton: dict[Registered[Any], Singleton[Any]] = {}

        self._logger = logger

    def get[T](self, interface: type[T], resolver: Resolver[T] | None = None) -> T:
        if interface not in self._interface_to_concretes:
            raise UnregisteredInterfaceError(interface)

        concretes = self._interface_to_concretes[interface]
        if len(concretes) == 0:
            raise UnregisteredInterfaceError(interface)
        if len(concretes) == 1:
            return self._get_singleton_instance(concretes[0])

        if resolver is None:
            self._logger.warning(
                f"Multiple concretes registered for interface {interface}. "
                "Using the first registered one."
            )
            return self._get_singleton_instance(concretes[0])

        register = resolver(concretes)
        return self._get_singleton_instance(register)

    def _get_singleton_instance[T](self, registered: Registered[T]) -> T:
        singleton = self._registered_to_singleton[registered]
        if singleton.instance is None:
            singleton.instance = registered.concrete()
        return cast(Any, singleton.instance)

    def register[T](
        self, interface: type[T], concrete: type[T], marker: Marker | None = None
    ) -> None:
        registered = Registered(concrete=concrete, marker=marker)
        self._interface_to_concretes[interface].append(registered)
        self._registered_to_singleton[registered] = Singleton()

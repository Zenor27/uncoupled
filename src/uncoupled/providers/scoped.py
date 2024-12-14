from collections import defaultdict
from collections.abc import Callable, Hashable
from dataclasses import dataclass
from logging import Logger
from typing import Any

from uncoupled.exception import ResolverError, UnregisteredInterfaceError
from uncoupled.providers.provider import Provider, Registered, Resolver, Marker


@dataclass(kw_only=True, slots=True)
class Scoped[I]:
    type: type[I]
    current_scope: Hashable | None = None
    current_instance: I | None = None


class ScopedProvider(Provider):
    def __init__(
        self, *, get_scope: Callable[[], Hashable], logger: Logger | None = None
    ) -> None:
        self._interface_to_concretes: dict[type, list[Registered[Any]]] = defaultdict(
            list
        )
        self._registered_to_scoped: dict[Registered[Any], Scoped[Any]] = {}

        self._get_scope = get_scope
        self._logger = logger or Logger("ScopedProvider")

    def get[T](self, interface: type[T], resolver: Resolver[T] | None = None) -> T:
        if interface not in self._interface_to_concretes:
            raise UnregisteredInterfaceError(interface)

        concretes = self._interface_to_concretes[interface]
        if len(concretes) == 0:
            raise UnregisteredInterfaceError(interface)

        if resolver is None:
            if len(concretes) > 1:
                self._logger.warning(
                    f"Multiple concretes registered for interface {interface}. "
                    "Using the first registered one."
                )
            return self._get_scoped_instance(concretes[0])

        try:
            register = resolver(concretes)
        except Exception:
            raise ResolverError(interface)

        return self._get_scoped_instance(register)

    def _get_scoped_instance[T](self, registered: Registered[T]) -> T:
        scoped = self._registered_to_scoped[registered]
        new_scope = self._get_scope()
        if scoped.current_instance is None or scoped.current_scope != new_scope:
            self._logger.debug(
                f"Creating new instance of {registered.concrete.__name__} "
                f"old scope was {scoped.current_scope}, new scope is {new_scope}"
            )
            scoped.current_scope = new_scope
            scoped.current_instance = registered.concrete()
        return scoped.current_instance

    def register[T](
        self, interface: type[T], concrete: type[T], marker: Marker | None = None
    ) -> None:
        registered = Registered(concrete=concrete, marker=marker, lifetime="scoped")
        self._interface_to_concretes[interface].append(registered)
        self._registered_to_scoped[registered] = Scoped(type=concrete)

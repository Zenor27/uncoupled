from collections import defaultdict
from logging import Logger
from dipy.exception import UnregisteredInterfaceError
from dipy.providers.provider import Provider, Registered, Resolver, Marker


class TransientProvider(Provider):
    def __init__(self, *, logger: Logger) -> None:
        self._interface_to_concretes: dict[type, list[Registered]] = defaultdict(list)
        self._logger = logger

    def get[T](self, interface: type[T], resolver: Resolver[T] | None = None) -> T:
        if interface not in self._interface_to_concretes:
            raise UnregisteredInterfaceError(interface)

        concretes = self._interface_to_concretes[interface]
        if len(concretes) == 0:
            raise UnregisteredInterfaceError(interface)
        if len(concretes) == 1:
            return concretes[0].concrete()

        if resolver is None:
            self._logger.warning(
                f"Multiple concretes registered for interface {interface}. "
                "Using the first registered one."
            )
            return concretes[0].concrete()

        return resolver(concretes).concrete()

    def register[T](
        self, interface: type[T], concrete: type[T], marker: Marker | None = None
    ) -> None:
        self._interface_to_concretes[interface].append(
            Registered(concrete=concrete, marker=marker)
        )

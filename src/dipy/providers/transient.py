from collections import defaultdict
from logging import Logger
from dipy.exception import ResolverError, UnregisteredInterfaceError
from dipy.providers.provider import Provider, Registered, Resolver, Marker


class TransientProvider(Provider):
    def __init__(self, *, logger: Logger | None = None) -> None:
        self._interface_to_concretes: dict[type, list[Registered]] = defaultdict(list)
        self._logger = logger or Logger("TransientProvider")

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
            return concretes[0].concrete()

        try:
            return resolver(concretes).concrete()
        except Exception:
            raise ResolverError(interface)

    def register[T](
        self, interface: type[T], concrete: type[T], marker: Marker | None = None
    ) -> None:
        self._interface_to_concretes[interface].append(
            Registered(concrete=concrete, marker=marker, lifetime="transient")
        )

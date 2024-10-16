from collections.abc import Callable, Hashable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal, Self, cast

from dipy.exception import (
    ContainerAlreadyCreatedError,
    ContainerNotCreatedError,
    UnregisteredInterfaceError,
)
from dipy.providers.provider import Provider, Marker, Resolver
from dipy.providers.scoped import ScopedProvider
from dipy.providers.singleton import SingletonProvider
from dipy.providers.transient import TransientProvider
import logging

if TYPE_CHECKING:
    from logging import _Level


_Lifetime = Literal["transient", "singleton", "scoped"]


@dataclass
class ScopedInstance[I]:
    current_scope: Hashable | None
    instance: I | None
    concrete: type[I]
    get_scope: Callable[[], Hashable]


def _default_get_scope() -> None:
    return None


class Container:
    _instance: "Container | None" = None

    @staticmethod
    def _get_instance() -> "Container":
        if Container._instance is None:
            raise ContainerNotCreatedError()

        return Container._instance

    def __init__(self, get_scope: Callable[[], Hashable], log_level: "_Level") -> None:
        self._logger = logging.getLogger("dipy")
        self._logger.setLevel(log_level)

        self._lifetime_to_provider: dict[_Lifetime, Provider] = {
            "transient": TransientProvider(logger=self._logger),
            "singleton": SingletonProvider(logger=self._logger),
            "scoped": ScopedProvider(get_scope=get_scope, logger=self._logger),
        }
        self._must_warn_about_default_get_scope = get_scope is _default_get_scope

    @classmethod
    def create(
        cls,
        get_scope: Callable[[], Hashable] = _default_get_scope,
        log_level: "_Level" = logging.WARNING,
    ) -> Self:
        if cls._instance is not None:
            raise ContainerAlreadyCreatedError()

        c = cls(get_scope, log_level)
        cls._instance = c
        return c

    def add_transient[I, C](
        self, interface: type[I], concrete: type[C], marker: Marker | None = None
    ) -> Self:
        self._logger.debug(f"Registering transient {interface} -> {concrete}")

        self._lifetime_to_provider["transient"].register(interface, concrete, marker)
        return self

    def add_singleton[I, C](
        self, interface: type[I], concrete: type[C], marker: Marker | None = None
    ) -> Self:
        self._logger.debug(f"Registering singleton {interface} -> {concrete}")

        self._lifetime_to_provider["singleton"].register(interface, concrete, marker)
        return self

    def add_scoped[I, C](
        self, interface: type[I], concrete: type[C], marker: Marker | None = None
    ) -> Self:
        self._logger.debug(f"Registering scoped {interface} -> {concrete}")

        if self._must_warn_about_default_get_scope:
            self._logger.warning(
                "Scoped instances will be created with the default scope. "
                "Therfore, they will be singletons. "
                "Consider providing a custom scope using the `get_scope` parameter."
            )
            self._must_warn_about_default_get_scope = False

        self._lifetime_to_provider["scoped"].register(interface, concrete, marker)
        return self

    def _get_concrete_instance[I](
        self, interface: type[I], resolver: Resolver[I] | None = None
    ) -> I:
        for provider in self._lifetime_to_provider.values():
            try:
                concrete = provider.get(interface, resolver)
                self._logger.debug(
                    f"Resolved {interface} to {concrete} with {provider.__class__.__name__}"
                )
                return concrete
            except UnregisteredInterfaceError:
                pass

        raise UnregisteredInterfaceError(interface)


def make_proxy_method(name: str):
    def proxy_method(self, *args: Any, **kwargs: Any) -> Any:
        if concrete := object.__getattribute__(self, "_concrete"):
            return getattr(concrete, name)(*args, **kwargs)

        interface = object.__getattribute__(self, "_interface")
        resolver = object.__getattribute__(self, "_resolver")
        concrete = Container._get_instance()._get_concrete_instance(interface, resolver)

        object.__setattr__(self, "_concrete", concrete)
        return getattr(concrete, name)(*args, **kwargs)

    return proxy_method


class LazyProxy[I]:
    def __init__(self, interface: type[I], resolver: Resolver | None = None) -> None:
        self._interface = interface
        self._resolver = resolver

        self._concrete: I | None = None

    __call__ = make_proxy_method("__call__")
    __getattribute__ = make_proxy_method("__getattribute__")
    __repr__ = make_proxy_method("__repr__")


def Depends[I](interface: type[I], resolver: Resolver[I] | None = None) -> I:
    return cast(I, LazyProxy[I](interface, resolver))

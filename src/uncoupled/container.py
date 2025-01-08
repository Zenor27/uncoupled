from collections.abc import Callable, Hashable
from dataclasses import dataclass
from inspect import signature
import inspect
from typing import TYPE_CHECKING, Any, Self, cast, get_type_hints
from uncoupled.lifetime import Lifetime

from uncoupled.exception import (
    ContainerAlreadyCreatedError,
    ContainerNotCreatedError,
    ResolverError,
    UnregisteredInterfaceError,
)
from uncoupled.providers.provider import Provider, Marker, Resolver
from uncoupled.providers.scoped import ScopedProvider
from uncoupled.providers.singleton import SingletonProvider
from uncoupled.providers.transient import TransientProvider
import logging

if TYPE_CHECKING:
    from logging import _Level


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
        self._logger = logging.getLogger("uncoupled")
        self._logger.setLevel(log_level)

        self._lifetime_to_provider: dict[Lifetime, Provider] = {
            "transient": TransientProvider(logger=self._logger),
            "singleton": SingletonProvider(logger=self._logger),
            "scoped": ScopedProvider(get_scope=get_scope, logger=self._logger),
        }
        self._must_warn_about_default_get_scope = get_scope is _default_get_scope

    @classmethod
    def _delete_instance(cls) -> None:
        Container._instance = None

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

    def get_concrete_instance[I](
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
            except ResolverError:
                pass

        raise UnregisteredInterfaceError(interface)


def make_not_wrapped_method(name: str):
    def _make_not_wrapped_method(self, *args: Any, **kwargs: Any) -> Any:
        if name in "__getattribute__" and ("_interface" in args or "_resolver" in args):
            return object.__getattribute__(self, *args, **kwargs)
        raise RuntimeError(
            "You are trying to call a Depends object, did you forget to use @inject ?"
        )

    return _make_not_wrapped_method


class _DependsMarker[I]:
    def __init__(self, interface: type[I], resolver: Resolver[I] | None = None) -> None:
        self._interface = interface
        self._resolver = resolver


for name, _ in inspect.getmembers(_DependsMarker):
    if name in {
        "__class__",
        "__new__",
        "__call__",
        "__init__",
        "__dict__",
        "__class_getitem__",
        "__parameters__",
        "__setattr__",
    }:
        continue
    setattr(_DependsMarker, name, make_not_wrapped_method(name))


def Depends[I](interface: type[I], resolver: Resolver[I] | None = None) -> I:
    return cast(I, _DependsMarker[I](interface, resolver))


def Resolve[I](
    interface: type[I], resolver: Resolver[I] | None = None
) -> Callable[[], I]:
    @inject
    def _resolve(i: I = Depends(interface, resolver)) -> I:
        return i

    return _resolve


def inject[F: Callable](func: F) -> F:
    def _uncoupled_inject_func(*args: Any, **kwargs: Any) -> Any:
        bound_args = signature(func).bind_partial(*args, **kwargs)
        bound_args.apply_defaults()

        for arg_name, arg_value in bound_args.arguments.items():
            if isinstance(arg_value, _DependsMarker):
                concrete_instance = Container._get_instance().get_concrete_instance(
                    arg_value._interface, arg_value._resolver
                )
                bound_args.arguments[arg_name] = concrete_instance

        return func(*bound_args.args, **bound_args.kwargs)

    return cast(F, _uncoupled_inject_func)

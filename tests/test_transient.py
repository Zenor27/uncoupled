from typing import Literal, Protocol

import pytest
from dipy.exception import ResolverError, UnregisteredInterfaceError
from dipy.providers.provider import Provider
from dipy.providers.transient import TransientProvider


class Interface(Protocol):
    type: Literal[42, 51]


class Impl(Interface):
    type = 42


class Impl2(Interface):
    type = 51


@pytest.fixture
def provider() -> Provider:
    return TransientProvider()


def test_get_should_instanciate(provider: Provider) -> None:
    provider.register(Interface, Impl)

    impl1 = provider.get(Interface)
    impl2 = provider.get(Interface)

    assert isinstance(impl1, Impl)
    assert isinstance(impl2, Impl)
    assert impl1 is not impl2


def test_get_unregistered(provider: Provider) -> None:
    with pytest.raises(UnregisteredInterfaceError):
        provider.get(Interface)


def test_multiple_concretes_no_resolver(provider: Provider) -> None:
    provider.register(Interface, Impl2)
    provider.register(Interface, Impl)

    impl = provider.get(Interface)
    assert isinstance(impl, Impl2)
    assert impl.type == 51


def test_multiple_concretes_with_resolver(provider: Provider) -> None:
    provider.register(Interface, Impl2)
    provider.register(Interface, Impl)

    impl = provider.get(
        Interface,
        lambda registered: next(r for r in registered if r.concrete.type == 42),
    )
    assert isinstance(impl, Impl)
    assert impl.type == 42


def test_multiple_concretes_with_marker(provider: Provider) -> None:
    provider.register(Interface, Impl2, "impl2")
    provider.register(Interface, Impl, "impl")

    impl = provider.get(
        Interface,
        resolver=lambda registered: next(r for r in registered if r.marker == "impl"),
    )
    assert isinstance(impl, Impl)
    assert impl.type == 42


def test_multiple_concretes_with_marker_not_found(provider: Provider) -> None:
    provider.register(Interface, Impl2, "impl2")
    provider.register(Interface, Impl, "impl")

    with pytest.raises(ResolverError):
        provider.get(
            Interface,
            resolver=lambda registered: next(
                r for r in registered if r.marker == "not_found"
            ),
        )

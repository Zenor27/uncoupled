from collections.abc import Generator
from typing import Protocol
import pytest

from uncoupled.container import Container, Depends


class Interface(Protocol):
    def foo(self) -> int: ...


class Impl(Interface):
    def foo(self) -> int:
        return 42


class Impl2(Interface):
    def foo(self) -> int:
        return 51


class Impl3(Interface):
    def foo(self) -> int:
        return 69


@pytest.fixture(autouse=True)
def init_container() -> Generator:
    c = Container.create()
    c.add_transient(Interface, Impl).add_scoped(
        Interface, Impl2, marker="scoped"
    ).add_singleton(Interface, Impl3)
    yield
    Container._delete_instance()


def test_injected() -> None:
    def foo(interface: Interface = Depends(Interface)) -> int:
        return interface.foo()

    assert foo() == 42


def test_injected_with_resolver() -> None:
    def foo(
        interface: Interface = Depends(
            Interface,
            resolver=lambda registered: next(
                r for r in registered if r.marker == "scoped"
            ),
        ),
    ) -> int:
        return interface.foo()

    assert foo() == 51


def test_injected_with_lifetime() -> None:
    def foo(
        interface: Interface = Depends(
            Interface,
            resolver=lambda registered: next(
                r for r in registered if r.lifetime == "singleton"
            ),
        ),
    ) -> int:
        return interface.foo()

    assert foo() == 69

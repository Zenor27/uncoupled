from collections.abc import Generator
from typing import Protocol
from uuid import uuid4
import pytest

from uncoupled.container import Container, Depends


class Interface(Protocol):
    def unique_id(self) -> str: ...


class Impl(Interface):
    def __init__(self) -> None:
        self._unique_id = str(uuid4())

    def unique_id(self) -> str:
        return self._unique_id


@pytest.fixture(autouse=True)
def init_container_scoped() -> Generator:
    c = Container.create(get_scope=lambda: uuid4())
    c.add_scoped(Interface, Impl)
    yield
    Container._delete_instance()


def test_instance_recreated() -> None:
    def get_instance(inst: Interface = Depends(Interface)) -> Interface:
        return inst

    i1 = get_instance()
    i2 = get_instance()

    assert i1.unique_id() != i2.unique_id()

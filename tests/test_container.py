from collections.abc import Generator
from typing import Protocol
import pytest

from dipy.container import Container
from dipy.exception import ContainerAlreadyCreatedError, ContainerNotCreatedError


@pytest.fixture()
def container() -> Generator[Container]:
    c = Container.create()
    yield c
    Container._delete_instance()


class Interface(Protocol): ...


class Impl(Interface): ...


def test_add_transient(container: Container) -> None:
    container.add_transient(Interface, Impl)

    impl = container.get_concrete_instance(Interface)
    assert isinstance(impl, Impl)


def test_add_singleton(container: Container) -> None:
    container.add_singleton(Interface, Impl)

    impl = container.get_concrete_instance(Interface)
    assert isinstance(impl, Impl)


def test_add_scoped(container: Container) -> None:
    container.add_scoped(Interface, Impl)

    impl = container.get_concrete_instance(Interface)
    assert isinstance(impl, Impl)


def test_container_already_created(container: Container) -> None:
    with pytest.raises(ContainerAlreadyCreatedError):
        Container.create()


def test_container_not_created() -> None:
    with pytest.raises(ContainerNotCreatedError):
        Container._get_instance()

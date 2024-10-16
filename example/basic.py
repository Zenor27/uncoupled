from typing import Protocol
from dipy.container import Container, Depends

import logging

logging.basicConfig(level=logging.DEBUG)


class Interface(Protocol):
    bar: int

    def foo(self, x: int) -> int: ...


class Concrete(Interface):
    def __init__(self) -> None:
        print("instanciating Concrete")
        self.bar = 42

    def foo(self, x: int) -> int:
        return x + 1


class SecondInterface(Protocol):
    def __call__(self, x: int) -> int: ...


class SecondConcrete(SecondInterface):
    def __init__(self, foo: Interface = Depends(Interface)) -> None:
        print("instanciating SecondConcrete")
        self.foo = foo

    def __call__(self, x: int) -> int:
        return self.foo.foo(x) + 51


def run(
    seed: int,
    foo_impl: Interface = Depends(Interface),
    second_impl: SecondInterface = Depends(SecondInterface),
) -> None:
    print(foo_impl.foo(seed))
    print(foo_impl.bar)

    print(second_impl(seed))


if __name__ == "__main__":
    container = Container.create()
    container.add_transient(SecondInterface, SecondConcrete)
    container.add_scoped(Interface, Concrete)
    run(41)

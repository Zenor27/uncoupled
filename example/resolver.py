from typing import Protocol

from dipy.container import Container, Depends


class Interface(Protocol):
    bar: int

    def foo(self, x: int) -> int: ...


class FirstImplementation(Interface):
    bar: int = 42

    def foo(self, x: int) -> int:
        return self.bar + x


class SecondImplementation(Interface):
    bar: int = 51

    def foo(self, x: int) -> int:
        return self.bar * x


def run(
    foo_impl: Interface = Depends(Interface),
) -> None:
    print(foo_impl.bar)
    print(foo_impl.foo(41))


if __name__ == "__main__":
    container = Container.create()
    container.add_transient(Interface, FirstImplementation)
    container.add_transient(Interface, SecondImplementation, marker="multi")

    run()

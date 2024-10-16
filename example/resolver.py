from typing import Protocol

from uncoupled.container import Container, Depends


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
    foo_first_impl: Interface = Depends(Interface),
    foo_second_impl: Interface = Depends(
        Interface,
        resolver=lambda registered: next(
            impl for impl in registered if impl.marker == "multi"
        ),
    ),
) -> None:
    print(foo_first_impl.foo(10))  # Should return 42 + 10 = 52
    print(foo_second_impl.foo(10))  # Should return 51 * 10 = 510


if __name__ == "__main__":
    container = Container.create()
    # Register the implementations with the same protocol but with a marker
    container.add_transient(Interface, FirstImplementation)
    container.add_transient(Interface, SecondImplementation, marker="multi")

    run()

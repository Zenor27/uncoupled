from typing import Protocol


class Provider(Protocol):
    def get[T](self, interface: type[T]) -> T: ...

    def register[T](self, interface: type[T], concrete: type[T]) -> None: ...

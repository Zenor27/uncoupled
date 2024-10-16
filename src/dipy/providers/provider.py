from collections.abc import Callable
from dipy.lifetime import Lifetime
from dataclasses import dataclass
from typing import Protocol


Marker = str


@dataclass(frozen=True, slots=True, kw_only=True)
class Registered[T]:
    concrete: type[T]
    lifetime: Lifetime
    marker: Marker | None = None


type Resolver[T] = Callable[[list[Registered[T]]], Registered[T]]


class Provider(Protocol):
    def get[T](self, interface: type[T], resolver: Resolver[T] | None = None) -> T: ...

    def register[T](
        self, interface: type[T], concrete: type[T], marker: Marker | None = None
    ) -> None: ...

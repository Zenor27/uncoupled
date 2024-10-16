# Uncoupled

[![Tests](https://github.com/Zenor27/uncoupled/actions/workflows/python-tests.yml/badge.svg?branch=main)](https://github.com/Zenor27/uncoupled/actions/workflows/python-tests.yml)

Modern Dependency Injection Container for Python 3.12+

## Usage

```python
from typing import Protocol

from uncoupled.container import Container, Depends


# Define the protocol (i.e the interface)
class IService(Protocol):
    def compute(self) -> int: ...


# Define a concrete implementation of the protocol
class ServiceImpl(IService):
    def compute(self) -> int:
        return 42


# Inject with `Depends` the required protocol
def my_function(svc: IService = Depends(IService)) -> None:
    print(svc.compute())  # Should return 42 !


if __name__ == "__main__":
    # Create a container and map a protocol to an implementation with a specific lifetime
    Container.create().add_transient(IService, ServiceImpl)

    # Call the function without arguments, `Depends` will take care of the injection
    my_function()
```

> Have a look at the `example` folder for more examples !

from abc import ABC, abstractmethod

class IStorage(ABC):
    @abstractmethod
    def write(self, data: list) -> None:
        ...

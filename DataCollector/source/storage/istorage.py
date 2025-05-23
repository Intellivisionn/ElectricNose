from abc import ABC, abstractmethod

class IStorage(ABC):
    @abstractmethod
    def write(self, data: list) -> None:
        ...

    @abstractmethod
    def set_filename(self, scent_name) -> None:
        ...
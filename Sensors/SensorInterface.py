from abc import ABC, abstractmethod

class Sensor(ABC):
    @abstractmethod
    def read_data(self) -> dict:
        pass

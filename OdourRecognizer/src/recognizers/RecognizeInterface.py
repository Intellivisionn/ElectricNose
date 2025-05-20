from abc import ABC, abstractmethod

class RecognizeInterface(ABC):
    @abstractmethod
    def recognize(self, data) -> dict:
        pass
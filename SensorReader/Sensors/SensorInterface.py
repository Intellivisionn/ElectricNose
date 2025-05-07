from abc import ABC, abstractmethod
from SensorReader.aspects.LoggingAspect import LoggingAspect


class Sensor(ABC):
    logger = LoggingAspect()

    @abstractmethod
    def read_data(self) -> dict:
        pass

    # Applies Logging aspect to every read_data method implemented by all subclasses of Sensor interface
    def __init_subclass__(cls):
        super().__init_subclass__()
        if 'read_data' in cls.__dict__:
            original_method = cls.__dict__['read_data']
            wrapped_method = Sensor.logger.log_method(original_method)
            setattr(cls, 'read_data', wrapped_method)
from DataCollector.source.storage.istorage import IStorage

class CloudStorage(IStorage):
    def __init__(self, bucket_name: str):
        # TODO: initialize your cloud SDK client
        self.bucket_name = bucket_name

    def write(self, data: list) -> None:
        # TODO: upload data to cloud storage
        raise NotImplementedError("CloudStorage not yet implemented")

    def set_filename(self, scent_name) -> None:
        # TODO: set filename
        raise NotImplementedError("CloudStorage not yet implemented")
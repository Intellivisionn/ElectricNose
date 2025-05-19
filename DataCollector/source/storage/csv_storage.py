from DataCollector.source.storage.istorage import IStorage

class CSVStorage(IStorage):
    def __init__(self, output_file: str):
        # TODO: implement CSV writing
        self.output_file = output_file

    def write(self, data: list) -> None:
        # TODO: write data to CSV
        raise NotImplementedError("CSVStorage not yet implemented")

    def set_filename(self, scent_name) -> None:
        # TODO: set filename
        raise NotImplementedError("CSVStorage not yet implemented")

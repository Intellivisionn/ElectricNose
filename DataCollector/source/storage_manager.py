import threading, time

class StorageManager(threading.Thread):
    def __init__(self, storages: list, data_source, interval: float = 5.0):
        super().__init__(daemon=True)
        self.storages = storages
        self.data_source = data_source
        self.interval = interval

    def run(self):
        while not self.data_source.stop_event.is_set():
            time.sleep(self.interval)
            # take a snapshot under lock
            with self.data_source.data_lock:
                snapshot = list(self.data_source.sensor_data_list)
            # write to each configured storage
            for store in self.storages:
                try:
                    store.write(snapshot)
                except Exception as e:
                    print(f"[StorageManager] Error in {store.__class__.__name__}: {e}")

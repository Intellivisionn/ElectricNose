from display_client import DisplayClient
import time

def run_model():
    # Your real model goes here
    print("Running model...")
    time.sleep(2)
    return "Lime", 0.92

if __name__ == "__main__":
    dm = DisplayClient(loading_duration=5, ventilation_duration=10)
    dm.on_predict = run_model
    dm.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        dm.stop()
        print("Shutdown.")
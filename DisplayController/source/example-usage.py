from .display_client import DisplayClient
import time
import random

def run_model():
    # Simulate a model that produces continuous predictions
    scents = ["Lime", "Peach", "Cherry", "Mint"]
    scent = random.choice(scents)
    conf  = random.uniform(0.5, 0.99)
    time.sleep(1)   # simulate processing time
    return scent, conf

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
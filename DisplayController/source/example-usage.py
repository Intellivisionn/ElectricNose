import time
import random
from display_client import DisplayClient, ConsoleDisplay  # or PiTFTDisplay

# Example prediction function
def run_model():
    scents = ["Lime", "Peach", "Cherry", "Mint"]
    scent = random.choice(scents)
    confidence = random.uniform(0.5, 0.99)
    time.sleep(1)  # simulate processing time
    return scent, confidence

if __name__ == "__main__":
    display = ConsoleDisplay()  # Or PiTFTDisplay() if on real hardware
    client = DisplayClient(display=display, loading_duration=5, ventilation_duration=10)
    client.on_predict = run_model

    client.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        client.stop()
        print("Shutdown.")

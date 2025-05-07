from display_client import DisplayManager
import time

def run_model():
    # Your real model goes here
    print("Running model...")
    time.sleep(2)
    return "Lime", 0.92

dm = DisplayManager(loading_duration=5, ventilation_duration=10)

try:
    while True:
        dm.step()

        # Inject prediction right after loading completes
        if dm.state == dm.state.PREDICTING and dm.prediction_data is None:
            scent, confidence = run_model()
            dm.provide_prediction(scent, confidence)

        time.sleep(1)
except KeyboardInterrupt:
    dm.cleanup()
    print("Shutdown.")
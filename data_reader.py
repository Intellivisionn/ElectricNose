import subprocess

def receive_serial_data():
    try:
        # Start the Arduino simulation process and read output
        process = subprocess.Popen(["/home/pi/ElectricNose-Arduino/arduino_sim"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        print("Listening for serial data...")

        while True:
            output = process.stdout.readline()
            if output:
                output = output.strip()
                if output.startswith("SENSOR_DATA:"):
                    sensor_value = output.split(":")[1].strip()
                    print(f"Received Sensor Data: {sensor_value}")
    except KeyboardInterrupt:
        print("Stopped receiving data.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    receive_serial_data()

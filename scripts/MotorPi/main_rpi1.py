import time
import serial
from StepperMotors_rpi1 import Motors
import mqttJoystickReceive as Receiver

ser = serial.Serial(
    port='/dev/ttyACM0',
    baudrate=9600,
    timeout=1
)

# Dictionary to store the sensor values
sensor_data = {
    'sens_photo': 0,
    'sens_humid': 0.0,
    'sens_temp': 0.0,
    'sens_lux': 0.0,
    'sens_range': 0,
    'led_red': False
}


def read_serial_data():
    """Read data from serial port and update sensor_data dictionary"""
    global sensor_data

    # Clear any existing data in the input buffer
    ser.flushInput()

    # Read data until buffer is empty
    buffer = ""
    start_time = time.time()
    timeout = 2  # Timeout in seconds

    while time.time() - start_time < timeout:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').strip()
            buffer += line + "\n"

            # Look for complete set of sensor readings
            if 'sens_photo' in line and len(buffer.strip()) > 10:
                parse_sensor_data(buffer)
                buffer = ""
                return True

    return False


def parse_sensor_data(data_string):
    """Parse the received data string into the sensor_data dictionary"""
    global sensor_data

    # Process each line
    for line in data_string.strip().split('\n'):
        if '=' in line:
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()

            if key in sensor_data:
                if key == 'led_red':
                    # Convert string 'true'/'false' to boolean
                    sensor_data[key] = (value.lower() == 'true')
                elif '.' in value:
                    # Handle floating point values
                    try:
                        sensor_data[key] = float(value)
                    except ValueError:
                        print(f"Could not convert {value} to float for {key}")
                else:
                    # Handle integer values
                    try:
                        sensor_data[key] = int(value)
                    except ValueError:
                        print(f"Could not convert {value} to int for {key}")


def main():
    # Initialize MQTT receiver and start it in the background
    receiver = Receiver.MqttJoystickReceive()
    receiver.main()

    # Initialize stepper motors
    stepper_motors = Motors()

    # Add a small delay to ensure MQTT connection is established
    time.sleep(1)

    try:
        while True:
            # Read and process sensor data
            if read_serial_data():
                print("Parsed sensor data:")
                for key, value in sensor_data.items():
                    print(f"{key}: {value}")

                if sensor_data['sens_range'] < 50 and sensor_data['sens_range'] != -1:
                    stepper_motors.run_both_motors_backward(10000)
                print("\n")

            # Check joystick position and control motors accordingly
            print(f"Current joystick_x value: {receiver.joystick_x}")

            if receiver.joystick_x > 700:
                print("Joystick forward")
                stepper_motors.run_both_motors_forward(10000)
            elif receiver.joystick_x < 400:
                print("Joystick backward")
                stepper_motors.run_both_motors_backward(10000)
            else:
                print("Joystick neutral")

            # Add a short delay to prevent CPU overload
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("Program stopped by user")
    finally:
        ser.close()
        print("Serial port closed")


if __name__ == "__main__":
    main()
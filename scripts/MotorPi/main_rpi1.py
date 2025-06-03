import time
import serial
import json
import paho.mqtt.client as mqtt
from StepperMotors_rpi1 import Motors
import mqttJoystickReceive as Receiver

# Set up serial connection
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


def on_connect(client, userdata, flags, rc):
    """Callback for when client connects to the broker"""
    connection_codes = {
        0: "Connection successful",
        1: "Connection refused - incorrect protocol version",
        2: "Connection refused - invalid client identifier",
        3: "Connection refused - server unavailable",
        4: "Connection refused - bad username or password",
        5: "Connection refused - not authorised"
    }
    print(f"Connected with result code {rc}: {connection_codes.get(rc, 'Unknown')}")


def on_publish(client, userdata, mid):
    """Callback for when a message is published"""
    print(f"Message published with id: {mid}")


# MQTT broker details
broker_address = "localhost"
broker_port = 1883
base_topic = "sensors"  # Base topic for all sensor data


def read_serial_data():
    """Read data from serial port and update sensor_data dictionary"""
    global sensor_data

    ser.flushInput()

    buffer = ""
    start_time = time.time()
    timeout = 2

    while time.time() - start_time < timeout:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').strip()
            buffer += line + "\n"

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
                    sensor_data[key] = (value.lower() == 'true')
                elif '.' in value:
                    try:
                        sensor_data[key] = float(value)
                    except ValueError:
                        print(f"Could not convert {value} to float for {key}")
                else:
                    try:
                        sensor_data[key] = int(value)
                    except ValueError:
                        print(f"Could not convert {value} to int for {key}")


def publish_sensor_data(mqtt_client):
    """Publish sensor data to MQTT topics"""

    for sensor, value in sensor_data.items():
        topic = f"{base_topic}/{sensor}"
        print(f"Publishing {sensor}: {value} to {topic}")
        mqtt_client.publish(topic, str(value), qos=0)


def main():
    # Initialize MQTT receiver and start it in the background
    receiver = Receiver.MqttJoystickReceive()
    receiver.main()

    # Initialize MQTT sender
    mqtt_sender = mqtt.Client(client_id="sensor_publisher")
    mqtt_sender.on_connect = on_connect
    mqtt_sender.on_publish = on_publish

    # Connect to MQTT broker
    print(f"Connecting to broker: {broker_address}:{broker_port}")
    mqtt_sender.connect(broker_address, broker_port, 60)
    mqtt_sender.loop_start()

    # Initialize stepper motors
    stepper_motors = Motors()

    time.sleep(1)

    try:
        while True:
            # Read and process sensor data
            if read_serial_data():
                print("Parsed sensor data:")
                for key, value in sensor_data.items():
                    print(f"{key}: {value}")

                publish_sensor_data(mqtt_sender)

                if sensor_data['sens_range'] < 50 and sensor_data['sens_range'] != -1:
                    stepper_motors.run_both_motors_backward(100000)
                print("\n")

            print(f"Current joystick_x value: {receiver.joystick_x}")

            if receiver.joystick_x > 700:
                print("Joystick forward")
                stepper_motors.run_both_motors_forward(100000)
            elif receiver.joystick_x < 400:
                print("Joystick backward")
                stepper_motors.run_both_motors_backward(100000)
            else:
                print("Joystick neutral")

            time.sleep(0.001)

    except KeyboardInterrupt:
        print("Program stopped by user")
    finally:
        ser.close()
        print("Serial port closed")
        mqtt_sender.loop_stop()
        mqtt_sender.disconnect()
        print("MQTT connection closed")


if __name__ == "__main__":
    main()
import serial
import time
import json
import paho.mqtt.client as mqtt


# MQTT Callbacks
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
broker_address = "192.168.176.33"
broker_port = 1883
base_topic = "joystick"

# Create and configure MQTT client
mqtt_client = mqtt.Client(client_id="sensor_publisher2")
mqtt_client.on_connect = on_connect
mqtt_client.on_publish = on_publish

# Connect to MQTT broker
print(f"Connecting to broker: {broker_address}:{broker_port}")
mqtt_client.connect(broker_address, broker_port, 60)
mqtt_client.loop_start()

try:
    ser = serial.Serial(
        port='/dev/ttyUSB0',
        baudrate=9600,
        timeout=1
    )
    print(f"Connected to serial port: {ser.name}")
except serial.SerialException as e:
    print(f"Error opening serial port: {e}")
    ser = None

# Dictionary to store the sensor values
sensor_data = {
    'sens_joy_x': 0,
    'sens_joy_y': 0,
}


def read_serial_data():
    """Read data from serial port and update sensor_data dictionary"""
    global sensor_data

    if ser is None:
        # Simulate joystick data if no serial connection
        import random
        sensor_data = {
            'sens_joy_x': random.randint(0, 1023),
            'sens_joy_y': random.randint(0, 1023),
        }
        return True

    # Clear any existing data in the input buffer
    ser.flushInput()

    # Read data until buffer is empty
    buffer = ""
    start_time = time.time()
    timeout = 2  # Timeout in seconds

    while time.time() - start_time < timeout:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            buffer += line + "\n"

            # Change this to look for joystick data pattern
            if 'joy_x' in line and len(buffer.strip()) > 5:
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
                    try:
                        sensor_data[key] = int(value)
                    except ValueError:
                        print(f"Could not convert {value} to")


time.sleep(1)

def publish_sensor_data():
    """Publish sensor data to MQTT topics"""
    # Publish all sensor data as a JSON payload to a single topic
    json_payload = json.dumps(sensor_data)
    print(f"Publishing all sensor data to {base_topic}/all")
    mqtt_client.publish(f"{base_topic}/all", json_payload, qos=0)

    # publish individual sensor values to their own topics
    for sensor, value in sensor_data.items():
        topic = f"{base_topic}/{sensor}"
        print(f"Publishing {sensor}: {value} to {topic}")
        mqtt_client.publish(topic, str(value), qos=0)


try:
    print("Starting sensor data collection and MQTT publishing...")
    print("Press Ctrl+C to stop")

    while True:
        if read_serial_data():
            # Print the parsed sensor data
            print("\nRead sensor data:")
            for key, value in sensor_data.items():
                print(f"{key}: {value} (type: {type(value).__name__})")

            # Publish the data to MQTT
            publish_sensor_data()

        time.sleep(1)

except KeyboardInterrupt:
    print("\nProgram stopped by user")
finally:
    if ser is not None:
        ser.close()
        print("Serial port closed")
    mqtt_client.loop_stop()
    mqtt_client.disconnect()
    print("MQTT connection closed")
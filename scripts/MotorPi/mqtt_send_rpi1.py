import serial
import time
import re
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


# MQTT broker details (modify these to match your setup)
broker_address = "localhost"  # or "127.0.0.1"
broker_port = 1883  # Default MQTT port
base_topic = "sensors"  # Base topic for all sensor data

# Create and configure MQTT client
mqtt_client = mqtt.Client(client_id="sensor_publisher")
mqtt_client.on_connect = on_connect
mqtt_client.on_publish = on_publish

# Connect to MQTT broker
print(f"Connecting to broker: {broker_address}:{broker_port}")
mqtt_client.connect(broker_address, broker_port, 60)
mqtt_client.loop_start()

# Set up serial connection
# Change the port according to your system
try:
    ser = serial.Serial(
        port='/dev/ttyACM0',  # Change this to match your system
        baudrate=9600,
        timeout=1
    )
    print(f"Connected to serial port: {ser.name}")
except serial.SerialException as e:
    print(f"Error opening serial port: {e}")
    # Create a placeholder for testing without actual hardware
    ser = None

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

    if ser is None:
        # Return simulated data for testing if no serial connection
        import random
        sensor_data = {
            'sens_photo': random.randint(0, 1023),
            'sens_humid': round(random.uniform(30, 70), 1),
            'sens_temp': round(random.uniform(18, 28), 1),
            'sens_lux': round(random.uniform(100, 1000), 1),
            'sens_range': random.randint(5, 100),
            'led_red': random.choice([True, False])
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
                        print(f"Could not convert {value} to")


# Wait to ensure MQTT connection is established
time.sleep(1)


def publish_sensor_data():
    """Publish sensor data to MQTT topics"""
    # Publish all sensor data as a JSON payload to a single topic
    json_payload = json.dumps(sensor_data)
    print(f"Publishing all sensor data to {base_topic}/all")
    mqtt_client.publish(f"{base_topic}/all", json_payload, qos=0)

    # Also publish individual sensor values to their own topics
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

        time.sleep(1)  # Wait a second before reading again

except KeyboardInterrupt:
    print("\nProgram stopped by user")
finally:
    # Clean up resources
    if ser is not None:
        ser.close()
        print("Serial port closed")
    mqtt_client.loop_stop()
    mqtt_client.disconnect()
    print("MQTT connection closed")
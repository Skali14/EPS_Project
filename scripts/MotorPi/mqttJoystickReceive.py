import paho.mqtt.client as mqtt


class MqttJoystickReceive:
    joystick_x = 504

    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code", rc)
        client.subscribe("joystick/sens_joy_x")

    def on_message(self, client, userdata, msg):
        print(f"Received on topic {msg.topic}: {msg.payload.decode()}")
        try:
            self.joystick_x = int(msg.payload.decode())
        except ValueError:
            print(f"Error converting joystick value: {msg.payload.decode()}")

    def main(self):
        broker_address = "localhost"  # Receiver Pi's IP (or localhost if self-hosted)
        # broker_port = 1883  # Default MQTT port
        client = mqtt.Client(protocol=mqtt.MQTTv311)
        client.on_connect = self.on_connect
        client.on_message = self.on_message

        client.connect(broker_address)
        # Start the loop in the background instead of blocking
        client.loop_start()

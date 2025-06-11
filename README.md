# Sensor Robot

"Sensor Robot" is an embedded project utilizing 2 Raspberry Pi's, one Arduino Nano and one Arduino Uno to achieve surveilance capabilities.

## Installation

### General

1. Install Python, using `sudo apt install python3`
2. Install the package manager `pip`, using `sudo apt install python3-pip`

3. Load the scripts from [here](scripts) onto the respective devices.
4. Create a virtual environment on both Pi's, using `python -m venv sensor_robot_env`
5. Activate the virtual environment on both Pi's, using `source sensor_robot_env/bin/activate`
6. Install the necessary packages, using `pip3 install requirements.txt`

### MQTT Setup
- Run these commands
  - `sudo apt upgrade && sudo apt dist-upgrade`
  - `sudo apt install mosquitto`
  - `sudo systemctl enable mosquitto.service`
  - `sudo mosquitto -d`
  - add these lines to `sudo nano /etc/mosquitto/conf.d/listener.conf`
    - listener 1883
    - allow_anonymous true

### Display Setup

- Run the command `sudo -E sensor_robot_env PATH=$PATH python3 adafruit-pitft.py`
  - Select configuration [1] for the display
  - Select rotation depending on your assembled robot
  - Select "No" for all following questions


### GStreamer Setup

- Install Gi for GStreamer, using `sudo apt-get install python3-gi gir1.2-gst-1.0 gir1.2-gst-app-1.0 gir1.2-glib-2.0`

### Arduino Nano Setup for Controller Pi

Use IDE such as Arduino IDE to upload/compile [arduino_nano_code.ino](scripts/SensorArduinoNano/arduino_nano_code.ino)

### Arduino Uno Setup for Motor Pi

Use IDE such as Arduino IDE to upload/compile [arduino_uno_code.ino](scripts/SensorArduinoUno/arduino_uno_code.ino)

## Usage

### Controller Pi

- Run the following scripts:
  - [`camera_receiver.py`](scripts/ControllerPi/camera_receiver.py)
  - [`mqtt_send_rpi2.py`](scripts/ControllerPi/mqtt_send_rpi2.py)
 
### Motor Pi

- Run the following scripts:
  - [`mqtt_send_rpi1.py`](scripts/MotorPi/mqtt_send_rpi1.py)
  - [`main_rpi1.py`](scripts/MotorPi/main_rpi1.py)
  - [`camera_sender.py`](scripts/MotorPi/camera_sender.py)



## Contributors

1. Michael Pittlik - k12226442
2. Simon Kadlec - k12222898
3. Felix Wild - k12216177
4. Cornelius Engl - k12216183
5. Felix Wöß - k12206357

## Acknowledgements

[Adafruit Display Setup Script](https://github.com/adafruit/Raspberry-Pi-Installer-Scripts/blob/main/adafruit-pitft.py)

## License

[MIT](https://choosealicense.com/licenses/mit/)

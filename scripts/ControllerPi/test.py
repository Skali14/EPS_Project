import serial
import time

# Serielle Verbindung zum Arduino
ser = serial.Serial(
    port='/dev/ttyUSB0',
    baudrate=9600,
    timeout=1
)

# Datenstruktur für Joystick-Werte
joystick_data = {
    'sens_joy_x': 0,
    'sens_joy_y': 0,
}


def read_serial_data():
    """Liest serielle Daten und aktualisiert das joystick_data-Dictionary"""
    global joystick_data

    ser.flushInput()
    buffer = ""
    start_time = time.time()
    timeout = 2  # Sekunden

    while time.time() - start_time < timeout:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            buffer += line + "\n"

            if 'joy_x' in line and len(buffer.strip()) > 10:
                parse_joystick_data(buffer)
                buffer = ""
                return True

    return False


def parse_joystick_data(data_string):
    """Parst Joystick-Daten aus dem seriellen String"""
    global joystick_data

    for line in data_string.strip().split('\n'):
        if '=' in line:
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()

            if key in joystick_data:
                if key == 'joy_btn':
                    joystick_data[key] = (value.lower() == 'true')
                else:
                    try:
                        joystick_data[key] = int(value)
                    except ValueError:
                        print(f"Fehler beim Konvertieren von {key}: {value}")


def main():
    try:
        while True:
            if read_serial_data():
                print("Joystick-Daten:")
                for key, value in joystick_data.items():
                    print(f"{key}: {value} ({type(value).__name__})")
                print("\n")

            time.sleep(0.2)

    except KeyboardInterrupt:
        print("Programm durch Benutzer beendet.")
    finally:
        ser.close()
        print("Serielle Verbindung geschlossen.")


if __name__ == "__main__":
    main()

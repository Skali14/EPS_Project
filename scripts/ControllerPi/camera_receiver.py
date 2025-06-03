import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstApp', '1.0')
from gi.repository import Gst, GstApp, GLib
import pygame
import paho.mqtt.client as mqtt
from paho.mqtt.client import CallbackAPIVersion
import os
import threading
import numpy as np
import time

# Global variables
VIDEO_PORT = 5000
VIDEO_WIDTH = 320
VIDEO_HEIGHT = 240
MQTT_BROKER_IP = "192.168.176.33"
MQTT_PORT = 1883
MQTT_TOPIC_TEMP = "sensors/sens_temp"
MQTT_TOPIC_HUMID = "sensors/sens_humid"
MQTT_TOPIC_PHOTO = "sensors/sens_photo"
MQTT_TOPIC_DIST = "sensors/sens_range"

# Pygame Setup
os.environ['SDL_FBDEV'] = '/dev/fb1'
pygame.init()
screen = pygame.display.set_mode((VIDEO_WIDTH, VIDEO_HEIGHT), 0, 0)
font = pygame.font.Font(None, 28)
small_font = pygame.font.Font(None, 20)

sensor_data = {
    "temperature": "N/A",
    "humidity": "N/A",
    "photo": "N/A",
    "distance": "N/A"
}
data_lock = threading.Lock()

# MQTT Client Setup
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("MQTT: Connected to Broker!")
        client.subscribe([(MQTT_TOPIC_TEMP, 0), (MQTT_TOPIC_PHOTO, 0), (MQTT_TOPIC_HUMID, 0), (MQTT_TOPIC_DIST, 0)])
    else:
        print(f"MQTT: Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    global sensor_data
    payload = msg.payload.decode()
    with data_lock:
        if msg.topic == MQTT_TOPIC_TEMP:
            sensor_data["temperature"] = payload
        elif msg.topic == MQTT_TOPIC_HUMID:
            sensor_data["humidity"] = payload
        elif msg.topic == MQTT_TOPIC_PHOTO:
            sensor_data["photo"] = payload
        elif msg.topic == MQTT_TOPIC_DIST:
            sensor_data["distance"] = payload

mqtt_client = mqtt.Client(client_id="ScreenPiSubscriber", callback_api_version=CallbackAPIVersion.VERSION1)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

def mqtt_thread_func():
    while True:
        try:
            print("Attempting MQTT connection...")
            mqtt_client.connect(MQTT_BROKER_IP, MQTT_PORT, 60)
            mqtt_client.loop_forever()
        except Exception as e:
            print(f"MQTT connection error: {e}. Retrying in 5s...")
            time.sleep(5)

# GStreamer Frame Handling
gst_frame = None
gst_frame_lock = threading.Lock()
frame_count = 0

def on_new_sample(appsink):
    global gst_frame, frame_count
    frame_count += 1

    sample = appsink.pull_sample()
    if sample:
        buf = sample.get_buffer()
        caps = sample.get_caps()

        # Extract frame data
        success, map_info = buf.map(Gst.MapFlags.READ)
        if success:
            try:
                # Get the actual format from caps
                structure = caps.get_structure(0)
                width = structure.get_int('width')[1]
                height = structure.get_int('height')[1]

                # Calculate expected size for RGB
                expected_size = width * height * 3
                if len(map_info.data) >= expected_size:
                    # Create numpy array with proper stride handling
                    frame_data = np.frombuffer(map_info.data[:expected_size], dtype=np.uint8)
                    frame_data = frame_data.reshape((height, width, 3))

                    with gst_frame_lock:
                        # Convert to Pygame surface (swap axes for width/height)
                        gst_frame = pygame.surfarray.make_surface(frame_data.swapaxes(0, 1))
                else:
                    print(f"Buffer size mismatch: got {len(map_info.data)}, expected {expected_size}")

            except Exception as e:
                print(f"Error processing frame: {e}")
            finally:
                buf.unmap(map_info)
        else:
            print("Failed to map buffer")
    else:
        print("No sample received")

    return Gst.FlowReturn.OK

# GStreamer Pipeline
print("Initializing GStreamer...")
Gst.init(None)

gst_pipeline_str = (
    f"udpsrc port={VIDEO_PORT} caps=\"application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)H264, payload=(int)96\" ! "
    f"rtpjitterbuffer latency=100 ! rtph264depay ! h264parse ! "
    f"avdec_h264 ! videoconvert ! video/x-raw,format=RGB,width={VIDEO_WIDTH},height={VIDEO_HEIGHT} ! "
    f"appsink name=mysink emit-signals=true max-buffers=1 drop=true sync=false"
)
pipeline = Gst.parse_launch(gst_pipeline_str)

appsink = pipeline.get_by_name('mysink')

appsink.set_property('emit-signals', True)
appsink.connect('new-sample', on_new_sample)

# Main Loop
if __name__ == "__main__":
    print("Starting MQTT thread...")
    mqtt_thread = threading.Thread(target=mqtt_thread_func, daemon=True)
    mqtt_thread.start()

    print("Starting GStreamer pipeline...")
    ret = pipeline.set_state(Gst.State.PLAYING)
    if ret == Gst.StateChangeReturn.FAILURE:
        print("ERROR: Failed to start GStreamer pipeline!")
        exit(1)

    running = True
    clock = pygame.time.Clock()
    frame_display_count = 0

    try:
        while running:
            screen.fill((0, 0, 0))

            current_frame = None
            with gst_frame_lock:
                if gst_frame:
                    current_frame = gst_frame.copy()

            if current_frame:
                frame_display_count += 1
                screen.blit(current_frame, (0, 0))
            else:
                no_video_text = font.render("No Video Signal", True, (255, 255, 255))
                text_rect = no_video_text.get_rect(center=(VIDEO_WIDTH//2, VIDEO_HEIGHT//2))
                screen.blit(no_video_text, text_rect)

            with data_lock:
                temp_text = font.render(f"Temp: {sensor_data['temperature']} C", True, (255, 255, 0))
                hum_text = font.render(f"Hum: {sensor_data['humidity']} %", True, (0, 255, 255))
                photo_text = font.render(f"Photo: {sensor_data['photo']} lm", True, (255, 255, 255))
                dist_text = font.render(f"Dist: {sensor_data['distance']} mm", True, (255, 0, 255))

            screen.blit(temp_text, (5, 5))
            screen.blit(hum_text, (5, 35))
            screen.blit(photo_text, (5, 65))
            screen.blit(dist_text, (5, 95))

            pygame.display.flip()
            clock.tick(30)

    except KeyboardInterrupt:
        print("Stopping Screen Receiver...")
    finally:
        print("Cleaning up...")
        pipeline.set_state(Gst.State.NULL)
        if mqtt_client.is_connected():
            mqtt_client.loop_stop()
            mqtt_client.disconnect()
        pygame.quit()
        print("Screen Receiver cleanup complete.")

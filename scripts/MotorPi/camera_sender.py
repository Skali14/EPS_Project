import subprocess
import time
import signal
import sys

# Global variables
SCREEN_PI_IP = "192.168.230.5"
VIDEO_PORT = 5000
VIDEO_WIDTH = 320
VIDEO_HEIGHT = 240
VIDEO_FRAMERATE = 20

video_process = None
gstreamer_process = None

def signal_handler(sig, frame):
    print("\nReceived interrupt signal, stopping...")
    cleanup()
    sys.exit(0)

def cleanup():
    global video_process, gstreamer_process
    processes = [
        ("libcamera", video_process),
        ("gstreamer", gstreamer_process)
    ]

    for name, process in processes:
        if process:
            print(f"Terminating {name} process...")
            process.terminate()
            try:
                process.wait(timeout=5)
                print(f"{name} process terminated gracefully")
            except subprocess.TimeoutExpired:
                print(f"{name} process didn't terminate gracefully, killing...")
                process.kill()
                process.wait()
                print(f"{name} process killed")

def create_gstreamer_command():
    libcamera_cmd = (
        f"libcamera-vid -t 0 --inline --nopreview "
        f"--width {VIDEO_WIDTH} --height {VIDEO_HEIGHT} --framerate {VIDEO_FRAMERATE} "
        f"--codec h264 --profile baseline --bitrate 1000000 "
        f"--intra 30 -o -"
    )

    gstreamer_cmd = (
        f"gst-launch-1.0 -v fdsrc ! h264parse ! rtph264pay config-interval=1 pt=96 mtu=1400 ! "
        f"udpsink host={SCREEN_PI_IP} port={VIDEO_PORT} sync=false"
    )

    return libcamera_cmd, gstreamer_cmd

def monitor_process(process):
    start_time = time.time()
    last_status_time = start_time

    while process.poll() is None:
        current_time = time.time()

        if current_time - last_status_time >= 10:
            runtime = current_time - start_time
            print(f"Video streaming running... ({runtime:.0f}s)")
            last_status_time = current_time

        time.sleep(1)

    return_code = process.returncode
    runtime = time.time() - start_time
    print(f"Video process ended after {runtime:.0f}s with return code: {return_code}")
    return return_code

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("=== Video Sender Starting ===")
    print(f"Target: {SCREEN_PI_IP}:{VIDEO_PORT}")
    print(f"Resolution: {VIDEO_WIDTH}x{VIDEO_HEIGHT} @ {VIDEO_FRAMERATE}fps")

    print("\n--- Starting Video Stream ---")
    libcamera_cmd, gstreamer_cmd = create_gstreamer_command()
    print(f"libcamera command: {libcamera_cmd}")
    print(f"GStreamer command: {gstreamer_cmd}")

    try:
        # Start libcamera-vid process
        print("Starting libcamera-vid...")
        video_process = subprocess.Popen(
            libcamera_cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )

        time.sleep(1)

        # Check if libcamera-vid started successfully
        if video_process.poll() is not None:
            stdout, stderr = video_process.communicate()
            print(f"libcamera-vid failed to start!")
            print(f"Return code: {video_process.returncode}")
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
            sys.exit(1)

        # Start GStreamer process
        print("Starting GStreamer...")
        gstreamer_process = subprocess.Popen(
            gstreamer_cmd,
            shell=True,
            stdin=video_process.stdout,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )

        video_process.stdout.close()

        print("Both processes started successfully!")
        print("Press Ctrl+C to stop...")

        # Monitor both processes
        start_time = time.time()
        last_status_time = start_time

        while True:
            # Check if either process has died
            libcamera_status = video_process.poll()
            gstreamer_status = gstreamer_process.poll()

            if libcamera_status is not None:
                print(f"libcamera-vid process ended with code: {libcamera_status}")
                _, stderr = video_process.communicate()
                if stderr:
                    print(f"libcamera-vid stderr: {stderr}")
                break

            if gstreamer_status is not None:
                print(f"GStreamer process ended with code: {gstreamer_status}")
                _, stderr = gstreamer_process.communicate()
                if stderr:
                    print(f"GStreamer stderr: {stderr}")
                break

            current_time = time.time()
            if current_time - last_status_time >= 10:
                runtime = current_time - start_time
                print(f"Video streaming running... ({runtime:.0f}s)")
                last_status_time = current_time

            time.sleep(1)

    except FileNotFoundError:
        print("ERROR: libcamera-vid or gst-launch-1.0 not found!")
        print("Make sure libcamera and GStreamer are installed")
    except Exception as e:
        print(f"ERROR starting video stream: {e}")
    finally:
        cleanup()
        print("Sender cleanup complete.")

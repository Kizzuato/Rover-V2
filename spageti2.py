from flask import Flask, jsonify, render_template, Response
import serial
import pynmea2
from smbus2 import SMBus
import threading
import time
import RPi.GPIO as GPIO
import atexit
import cv2

app = Flask(__name__)

# =========================================================
# GPS
# =========================================================

gps_port = '/dev/serial0'
gps_baud = 9600

# Dummy awal
gps_data = {
    "lat": 11,
    "lon": 16,
    "alt": 41
}


def read_gps():
    global gps_data

    try:
        ser = serial.Serial(
            gps_port,
            gps_baud,
            timeout=1
        )

        time.sleep(2)

        print("GPS started")

        while True:

            line = ser.readline().decode(
                'ascii',
                errors='ignore'
            ).strip()

            if line.startswith('$GNGGA') or line.startswith('$GPGGA'):

                try:
                    msg = pynmea2.parse(line)

                    gps_data['lat'] = msg.latitude
                    gps_data['lon'] = msg.longitude
                    gps_data['alt'] = msg.altitude

                except pynmea2.ParseError:
                    continue

    except Exception as e:
        print("GPS error:", e)


# =========================================================
# MPU6050
# =========================================================

bus = SMBus(1)

MPU_ADDR = 0x68

try:

    bus.write_byte_data(
        MPU_ADDR,
        0x6B,
        0x00
    )

    print("MPU6050 initialized")

except Exception as e:
    print("MPU init error:", e)


INT_PIN = 4

GPIO.setmode(GPIO.BCM)

GPIO.setup(
    INT_PIN,
    GPIO.IN,
    pull_up_down=GPIO.PUD_UP
)


imu_data = {
    "acc": [0, 0, 0],
    "gyro": [0, 0, 0],
    "mag": [0, 0, 0],
    "heading": 0
}


def read_word(addr, reg):

    high = bus.read_byte_data(
        addr,
        reg
    )

    low = bus.read_byte_data(
        addr,
        reg + 1
    )

    val = (high << 8) + low

    if val >= 0x8000:
        val = -((65535 - val) + 1)

    return val


def read_imu_polling():

    global imu_data

    while True:

        try:

            # Accelerometer
            ax = read_word(
                MPU_ADDR,
                0x3B
            )

            ay = read_word(
                MPU_ADDR,
                0x3D
            )

            az = read_word(
                MPU_ADDR,
                0x3F
            )

            # Gyroscope
            gx = read_word(
                MPU_ADDR,
                0x43
            )

            gy = read_word(
                MPU_ADDR,
                0x45
            )

            gz = read_word(
                MPU_ADDR,
                0x47
            )

            imu_data['acc'] = [
                ax,
                ay,
                az
            ]

            imu_data['gyro'] = [
                gx,
                gy,
                gz
            ]

            time.sleep(0.05)

        except Exception as e:

            print(
                "IMU read error:",
                e
            )

            time.sleep(0.1)


# =========================================================
# CAMERA
# =========================================================

CAMERA_DEVICE1 = 0
CAMERA_DEVICE2 = 2


# =========================================================
# Open Camera 1
# =========================================================

camera1 = cv2.VideoCapture(
    CAMERA_DEVICE1,
    cv2.CAP_V4L2
)

# TAMBAHAN: Set format ke MJPG (Hardware encoding dari kamera)
camera1.set(
    cv2.CAP_PROP_FOURCC, 
    cv2.VideoWriter_fourcc(*'MJPG')
)

camera1.set(
    cv2.CAP_PROP_FRAME_WIDTH,
    640
)

camera1.set(
    cv2.CAP_PROP_FRAME_HEIGHT,
    480
)

camera1.set(
    cv2.CAP_PROP_FPS,
    30
)


# =========================================================
# Open Camera 2
# =========================================================

camera2 = cv2.VideoCapture(
    CAMERA_DEVICE2,
    cv2.CAP_V4L2
)

# TAMBAHAN: Set format ke MJPG (Hardware encoding dari kamera)
camera2.set(
    cv2.CAP_PROP_FOURCC, 
    cv2.VideoWriter_fourcc(*'MJPG')
)

camera2.set(
    cv2.CAP_PROP_FRAME_WIDTH,
    640
)

camera2.set(
    cv2.CAP_PROP_FRAME_HEIGHT,
    480
)

camera2.set(
    cv2.CAP_PROP_FPS,
    30
)


# =========================================================
# Camera Status
# =========================================================

if camera1.isOpened():

    print(
        "Camera 1 berhasil dibuka: /dev/video0"
    )

else:

    print(
        "ERROR: Camera 1 gagal dibuka"
    )


if camera2.isOpened():

    print(
        "Camera 2 berhasil dibuka: /dev/video2"
    )

else:

    print(
        "ERROR: Camera 2 gagal dibuka"
    )


# =========================================================
# JPEG Buffer
# =========================================================

jpeg1 = None
jpeg2 = None


jpeg_lock1 = threading.Lock()
jpeg_lock2 = threading.Lock()


# =========================================================
# CAMERA THREAD 1
# =========================================================

def camera_thread1():

    global jpeg1

    print(
        "Camera thread 1 started"
    )

    while True:

        try:

            ret, frame = camera1.read()

            if not ret or frame is None:

                print(
                    "Camera 1 gagal membaca frame"
                )

                time.sleep(0.1)

                continue


            # Convert frame -> JPEG

            ret, encoded = cv2.imencode(
                '.jpg',
                frame,
                [
                    cv2.IMWRITE_JPEG_QUALITY,
                    80
                ]
            )

            if not ret:

                continue


            # Simpan JPEG terbaru

            with jpeg_lock1:

                jpeg1 = encoded.tobytes()


        except Exception as e:

            print(
                "Camera 1 error:",
                e
            )

            time.sleep(0.1)


# =========================================================
# CAMERA THREAD 2
# =========================================================

def camera_thread2():

    global jpeg2

    print(
        "Camera thread 2 started"
    )

    while True:

        try:

            ret, frame = camera2.read()

            if not ret or frame is None:

                print(
                    "Camera 2 gagal membaca frame"
                )

                time.sleep(0.1)

                continue


            # Convert frame -> JPEG

            ret, encoded = cv2.imencode(
                '.jpg',
                frame,
                [
                    cv2.IMWRITE_JPEG_QUALITY,
                    80
                ]
            )

            if not ret:

                continue


            # Simpan JPEG terbaru

            with jpeg_lock2:

                jpeg2 = encoded.tobytes()


        except Exception as e:

            print(
                "Camera 2 error:",
                e
            )

            time.sleep(0.1)


# =========================================================
# STREAM CAMERA 1
# =========================================================

def generate_frames_camera1():

    while True:

        with jpeg_lock1:

            data = jpeg1


        if data is None:

            time.sleep(0.05)

            continue


        yield (

            b'--frame\r\n'

            b'Content-Type: image/jpeg\r\n'

            b'Content-Length: ' +

            str(
                len(data)
            ).encode() +

            b'\r\n\r\n' +

            data +

            b'\r\n'
        )


# =========================================================
# STREAM CAMERA 2
# =========================================================

def generate_frames_camera2():

    while True:

        with jpeg_lock2:

            data = jpeg2


        if data is None:

            time.sleep(0.05)

            continue


        yield (

            b'--frame\r\n'

            b'Content-Type: image/jpeg\r\n'

            b'Content-Length: ' +

            str(
                len(data)
            ).encode() +

            b'\r\n\r\n' +

            data +

            b'\r\n'
        )


# =========================================================
# ROUTE: HOME
# =========================================================

@app.route('/')
def index():

    return render_template(
        'index.html'
    )


# =========================================================
# ROUTE: SENSOR DATA
# =========================================================

@app.route('/data')
def data():

    return jsonify({

        "gps": gps_data,

        "imu": imu_data

    })


# =========================================================
# ROUTE: CAMERA 1
# =========================================================

@app.route('/video1')
def video1():

    return Response(

        generate_frames_camera1(),

        mimetype=
        'multipart/x-mixed-replace; boundary=frame'

    )


# =========================================================
# ROUTE: CAMERA 2
# =========================================================

@app.route('/video2')
def video2():

    return Response(

        generate_frames_camera2(),

        mimetype=
        'multipart/x-mixed-replace; boundary=frame'

    )


# =========================================================
# SNAPSHOT CAMERA 1
# =========================================================

@app.route('/snapshot1')
def snapshot1():

    with jpeg_lock1:

        data = jpeg1


    if data is None:

        return jsonify({

            "error":
            "Camera 1 belum siap"

        }), 500


    return Response(

        data,

        mimetype='image/jpeg'

    )


# =========================================================
# SNAPSHOT CAMERA 2
# =========================================================

@app.route('/snapshot2')
def snapshot2():

    with jpeg_lock2:

        data = jpeg2


    if data is None:

        return jsonify({

            "error":
            "Camera 2 belum siap"

        }), 500


    return Response(

        data,

        mimetype='image/jpeg'

    )


# =========================================================
# CLEANUP
# =========================================================

def cleanup():

    print(
        "\nCleaning up..."
    )


    try:

        GPIO.cleanup()

    except Exception:

        pass


    try:

        if camera1.isOpened():

            camera1.release()

    except Exception:

        pass


    try:

        if camera2.isOpened():

            camera2.release()

    except Exception:

        pass


    try:

        bus.close()

    except Exception:

        pass


    print(
        "Cleanup complete"
    )


atexit.register(
    cleanup
)


# =========================================================
# MAIN
# =========================================================

if __name__ == '__main__':

    print(
        "======================================"
    )

    print(
        "ROV Dashboard Starting..."
    )

    print(
        "======================================"
    )


    # GPS thread

  #  threading.Thread(

   #     target=read_gps,

    #   daemon=True

    #).start()


    # IMU thread

    #threading.Thread(

#        target=read_imu_polling,

#        daemon=True

 #   ).start()


    # Camera 1 thread

    threading.Thread(

        target=camera_thread1,

        daemon=True

    ).start()


    # Camera 2 thread

    threading.Thread(

        target=camera_thread2,

        daemon=True

    ).start()


    print(
        "GPS thread started"
    )

    print(
        "IMU thread started"
    )

    print(
        "Camera 1 thread started"
    )

    print(
        "Camera 2 thread started"
    )


    print(
        "======================================"
    )

    print(
        "Flask running on port 5000"
    )

    print(
        "Camera 1 : /video1"
    )

    print(
        "Camera 2 : /video2"
    )

    print(
        "Sensor   : /data"
    )

    print(
        "======================================"
    )


    app.run(

        host='0.0.0.0',

        port=5000,

        debug=False,

        threaded=True

    )


import cv2
import time
import threading

cam1 = cv2.VideoCapture(0, cv2.CAP_V4L2)
cam2 = cv2.VideoCapture(2, cv2.CAP_V4L2)

cam1.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cam1.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

cam2.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cam2.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

print("CAM1:", cam1.isOpened())
print("CAM2:", cam2.isOpened())


def read_cam1():
    while True:
        ret, frame = cam1.read()

        if not ret:
            print("CAM1 gagal")
            continue

        print("CAM1 OK", frame.shape)


def read_cam2():
    while True:
        ret, frame = cam2.read()

        if not ret:
            print("CAM2 gagal")
            continue

        print("CAM2 OK", frame.shape)


t1 = threading.Thread(target=read_cam1, daemon=True)
t2 = threading.Thread(target=read_cam2, daemon=True)

t1.start()
t2.start()x

while True:
    time.sleep(1)

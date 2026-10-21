import cv2
import socket
import time

# Konfigurasi Target Penerima (Komputer/Laptop)
TARGET_IP = "10.37.36.214"
TARGET_PORT = 5005

# Inisialisasi Socket UDP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Inisialisasi Kamera (0 untuk default USB camera / Picam dengan V4L2)

cap = cv2.VideoCapture(0, cv2.CAP_V4L2)

# Set format pixel mentah ke MJPG (membantu banyak jenis webcam USB)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Set resolusi kamera lebih rendah agar ukuran paket aman untuk UDP (< 65 KB)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 480)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)

# Kualitas kompresi JPEG (0 - 100, default ~50-70 untuk keseimbangan bandwidth & kualitas)
ENCODE_PARAM = [int(cv2.IMWRITE_JPEG_QUALITY), 50]

print(f"Streaming dimulai ke {TARGET_IP}:{TARGET_PORT}...")

try:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Gagal membaca frame kamera.")
            break

        # Encode frame ke format JPEG
        result, encoded_img = cv2.imencode('.jpg', frame, ENCODE_PARAM)

        if result:
            data = encoded_img.tobytes()

            # Batas aman payload 1 paket UDP adalah 65,507 bytes
            if len(data) < 65507:
                sock.sendto(data, (TARGET_IP, TARGET_PORT))
            else:
                print("Ukuran frame terlalu besar untuk 1 paket UDP! Turunkan resolusi/kualitas.")

        # Jeda tipis untuk kontrol framerate (~30 FPS)
        time.sleep(0.03)

except KeyboardInterrupt:
    print("\nStreaming dihentikan oleh pengguna.")

finally:
    cap.release()
    sock.close()
    print("Kamera dan socket ditutup."

from flask import Flask, Response, jsonify
import cv2

app = Flask(__name__)

# Inisialisasi kamera menggunakan backend V4L2 (sesuai yang berhasil sebelumnya)
cap = cv2.VideoCapture(1, cv2.CAP_V4L2)

# Set resolusi (sesuaikan kebutuhan, 640x480 cukup optimal untuk stream web)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

def generate_frames():
    while True:
        success, frame = cap.read()
        if not success:
            break

        # Kompres frame menjadi JPEG untuk efisiensi bandwidth
        ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
        if not ret:
            continue

        frame_bytes = buffer.tobytes()

        # Stream menggunakan format multipart/x-mixed-replace (Standar Web Stream)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

# ----------------------------------------------------
# DAFTAR ENDPOINT API
# ----------------------------------------------------

# 1. Endpoint untuk mengecek status API & Kamera (Berupa JSON)
@app.route('/api/status', methods=['GET'])
def check_status():
    return jsonify({
        "status": "success",
        "message": "API Camera Raspberry Pi berjalan normal.",
        "camera_opened": cap.isOpened()
    })

# 2. Endpoint utama untuk mengambil Video Stream
@app.route('/api/video_feed', methods=['GET'])
def video_feed():
    # GCS akan memanggil endpoint ini
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    print("🚀 API Server berjalan! Akses stream di: http://<IP_RASPBERRY_PI>:5000/api/video_feed")
    # host='0.0.0.0' memastikan API bisa diakses dari jaringan lokal (laptop)
    app.run(host='0.0.0.0', port=5000, threaded=True)

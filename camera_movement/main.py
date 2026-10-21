import sys
import readchar
from gpiozero import AngularServo
from gpiozero.pins.pigpio import PiGPIOFactory

# Menggunakan PWM hardware via pigpio untuk sinyal servo yang stabil dan mulus
try:
    factory = PiGPIOFactory()
except Exception:
    factory = None

# Konfigurasi Pulsa MG996R (0.5ms - 2.5ms)
servo = AngularServo(
    pin=18,                            # Pin GPIO 18
    min_angle=0, 
    max_angle=180,
    min_pulse_width=0.5 / 1000,        # 0.5 ms
    max_pulse_width=2.5 / 1000,        # 2.5 ms
    pin_factory=factory
)

# Inisialisasi posisi dan langkah sudut
current_angle = 90
step = 5  # Perubahan sudut per tekan tombol
servo.angle = current_angle

print("=" * 45)
print(" KONTROL SERVO HEADLESS (SSH) - MG996R")
print("=" * 45)
print(" [A] / [Panah Kiri]  : Putar Kiri (-5°)")
print(" [D] / [Panah Kanan] : Putar Kanan (+5°)")
print(" [W]                 : Putar Kiri Cepat (-15°)")
print(" [S]                 : Putar Kanan Cepat (+15°)")
print(" [C]                 : Reset Posisi Tengah (90°)")
print(" [Q]                 : Keluar")
print("-" * 45)
print(f"Sudut Sekarang: {current_angle}°")

def update_angle(new_angle):
    global current_angle
    # Batasi nilai di rentang 0 - 180 derajat
    current_angle = max(0, min(180, new_angle))
    servo.angle = current_angle
    print(f"\r[INFO] Sudut Servo: {current_angle:3d}°  ", end="", flush=True)

try:
    while True:
        # Membaca karakter tombol dari terminal SSH tanpa perlu menekan Enter
        key = readchar.readkey()

        if key in (readchar.key.LEFT, 'a', 'A'):
            update_angle(current_angle - step)
        elif key in (readchar.key.RIGHT, 'd', 'D'):
            update_angle(current_angle + step)
        elif key in ('w', 'W'):
            update_angle(current_angle - 15)
        elif key in ('s', 'S'):
            update_angle(current_angle + 15)
        elif key in ('c', 'C'):
            update_angle(90)
        elif key in ('q', 'Q', readchar.key.CTRL_C):
            print("\n\nKeluar dari program...")
            break

finally:
    # Mematikan pulsa PWM agar servo tidak terus dengung/panas
    servo.detach()
    print("Sinyal servo dilepas. Selesai.")

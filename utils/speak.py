from pydub import AudioSegment
from pydub.playback import play
import numpy as np
import threading
import time
from time import sleep
import random

# Optional Raspberry Pi hardware support
try:
    import gpiozero
    from gpiozero.pins.pigpio import PiGPIOFactory
    _HW_AVAILABLE = True
except Exception:
    gpiozero = None
    PiGPIOFactory = None
    _HW_AVAILABLE = False


class _NoOp:
    def __getattr__(self, _):
        return self
    def __call__(self, *args, **kwargs):
        return self
    @property
    def angle(self):
        return 0
    @angle.setter
    def angle(self, _):
        pass


if _HW_AVAILABLE:
    pigpioFactory = PiGPIOFactory()
    mouthServo = gpiozero.AngularServo(27, min_angle=0, max_angle=180, pin_factory=pigpioFactory)
    armServo1 = gpiozero.AngularServo(14, min_angle=0, max_angle=180, pin_factory=pigpioFactory)
    armServo2 = gpiozero.AngularServo(15, min_angle=0, max_angle=180, pin_factory=pigpioFactory)
    car = gpiozero.Robot(left=gpiozero.Motor(3, 2), right=gpiozero.Motor(17, 4))
else:
    mouthServo = _NoOp()
    armServo1 = _NoOp()
    armServo2 = _NoOp()
    car = _NoOp()

# Initialize mouth position
try:
    mouthServo.angle = 0
except Exception:
    pass

def rotate(degrees):
    print(f"Servo -> {degrees:.1f}°")
    mouthServo.angle = degrees


def animate_servo_with_audio(audio, update_interval=0.01, max_angle=30):
    samples = np.array(audio.get_array_of_samples()).astype(np.float32)
    samples /= np.max(np.abs(samples))  # normalize

    sample_rate = audio.frame_rate
    duration_per_sample = 1.0 / sample_rate
    step = int(update_interval / duration_per_sample)

    time.sleep(0.75)
    start_time = time.time()

    arm1cd = start_time + random.uniform(2, 5)
    arm2cd = start_time + random.uniform(2, 5)
    arm1Target = random.uniform(0, 90)
    arm2Target = random.uniform(0, 90)
    for i in range(0, len(samples), step):
        if time.time() - arm1cd > 0:
            arm1Target = random.uniform(0, 90)
            arm1cd += random.uniform(2, 5)
        if time.time() - arm2cd > 0:
            arm2Target = random.uniform(0, 90)
            arm2cd += random.uniform(2, 5)

        speed = 1
        if arm1Target != armServo1.angle:
            armServo1.angle += max(-speed, min(speed, arm1Target - armServo1.angle))
        if arm2Target != armServo2.angle:
            armServo2.angle += max(-speed, min(speed, arm2Target - armServo2.angle))
        

        chunk = samples[i:i+step]
        if len(chunk) == 0:
            break

        rms = np.sqrt(np.mean(chunk**2))
        angle = rms * max_angle  # map to 0–30 degrees

        rotate(angle)

        # Sync with playback
        expected_time = start_time + (i / sample_rate)
        now = time.time()
        delay = expected_time - now
        if delay > 0:
            time.sleep(delay)

    # small buffer so playback can finish naturally
    time.sleep(0.25)


def play_audio(audio):
    play(audio)


def speak_audio(audio: AudioSegment, max_angle: int = 60):
    """Play an AudioSegment while animating the mouth/arms to the audio.

    This function starts playback in a background thread and synchronizes
    servo animation based on the audio's RMS over small windows.

    On environments without Raspberry Pi GPIO libraries, servo control
    becomes a no-op but audio still plays.
    """
    # Ensure mono for consistent RMS behavior
    audio_mono = audio.set_channels(1)

    t = threading.Thread(target=play_audio, args=(audio_mono,), daemon=True)
    t.start()

    animate_servo_with_audio(audio_mono, max_angle=max_angle)
    t.join()


if __name__ == "__main__":
    audio = AudioSegment.from_file("mp3s/bee.mp3")
    speak_audio(audio, max_angle=60)

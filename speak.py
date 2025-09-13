from pydub import AudioSegment
from pydub.playback import play
import numpy as np
import threading
import time

# Fake servo control function


def rotate(degrees):
    print(f"Servo -> {degrees:.1f}°")


def animate_servo_with_audio(audio, update_interval=0.05, max_angle=30):
    samples = np.array(audio.get_array_of_samples()).astype(np.float32)
    samples /= np.max(np.abs(samples))  # normalize

    sample_rate = audio.frame_rate
    duration_per_sample = 1.0 / sample_rate
    step = int(update_interval / duration_per_sample)

    start_time = time.time()

    for i in range(0, len(samples), step):
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


if __name__ == "__main__":
    audio = AudioSegment.from_file("mp3s/bee.mp3").set_channels(1)

    # Start playback in another thread
    t = threading.Thread(target=play_audio, args=(audio,))
    t.start()

    # Animate servo while audio plays
    animate_servo_with_audio(audio, max_angle=45)

    t.join()

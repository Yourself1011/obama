import random
import time
import os
import pygame

# Folder with MP3 files
AUDIO_DIR = "./mp3s"

# Random interval range (seconds)
MIN_WAIT = 5
MAX_WAIT = 15


def get_audio_files():
    return [
        os.path.join(AUDIO_DIR, f)
        for f in os.listdir(AUDIO_DIR)
        if f.lower().endswith(".mp3")
    ]


def play_audio(file):
    pygame.mixer.music.load(file)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)


def main():
    pygame.mixer.init()
    while True:
        audio_files = get_audio_files()
        if not audio_files:
            print("No MP3 files found in ./mp3s")
            time.sleep(5)
            continue

        random.shuffle(audio_files)
        for file in audio_files:
            print(f"Playing: {os.path.basename(file)}")
            play_audio(file)
            wait_time = random.uniform(MIN_WAIT, MAX_WAIT)
            print(f"Waiting {wait_time:.2f} seconds...")
            time.sleep(wait_time)


if __name__ == "__main__":
    main()

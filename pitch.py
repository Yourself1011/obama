#!/usr/bin/env python3
"""
Script to play pitch.mp3 using the speak.py utility.
This will play the audio while animating servos (if hardware is available).
"""

from pydub import AudioSegment
from utils.speak import speak_audio

def main():
    """Load and play the pitch.mp3 file using the speak utility."""
    try:
        # Load the pitch.mp3 file
        audio = AudioSegment.from_file("mp3s/pitch.mp3")
        
        print("Playing pitch.mp3...")
        # Use the speak_audio function to play with servo animation
        speak_audio(audio, max_angle=60)
        
        print("Finished playing pitch.mp3")
        
    except FileNotFoundError:
        print("Error: pitch.mp3 not found in mp3s/ directory")
    except Exception as e:
        print(f"Error playing audio: {e}")

if __name__ == "__main__":
    main()

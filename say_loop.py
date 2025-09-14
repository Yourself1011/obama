import os
import tempfile
import time
from dotenv import load_dotenv
from pydub import AudioSegment

from utils.generate import generate_tts, fetch_latest_mp3, save_mp3
from utils.speak import speak_audio


def main():
    print("=== Obama Say Loop ===")
    print("Type a line and press Enter; Obama will say it. Type 'q' to quit.")

    # Load env for FINESHARE_API_TOKEN
    load_dotenv()
    if not os.getenv("FINESHARE_API_TOKEN", "").strip():
        print("Warning: FINESHARE_API_TOKEN is not set. Add it to your .env.")

    while True:
        try:
            text = input("Text> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break
        if text.lower() in {"q", "quit", "exit"}:
            print("Goodbye.")
            break
        if not text:
            continue

        try:
            print("Generating Obama voice...")
            generate_tts(text)
            print("Waiting for audio to be ready...")
            mp3_url = fetch_latest_mp3()
            with tempfile.TemporaryDirectory() as td:
                out_path = os.path.join(td, "tts.mp3")
                save_mp3(mp3_url, out_path, volume_factor=4.0)
                audio = AudioSegment.from_file(out_path, format="mp3")
                print("Playing...")
                speak_audio(audio)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(1)


if __name__ == "__main__":
    main()

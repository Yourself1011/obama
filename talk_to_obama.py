import os
import sys
import time
import tempfile
import threading
from typing import List, Optional
import numpy as np
from pydub import AudioSegment
from pydub.playback import play
from openai import OpenAI
from dotenv import load_dotenv
import random

# Obama TTS helpers and speaker
from utils.generate import generate_tts, fetch_latest_mp3, save_mp3
from utils.speak import speak_audio
from utils.transcribe import stream_transcribe_until_enter


"""
Note: STT is now handled by utils.transcribe.stream_transcribe_until_enter for
low-latency local Whisper transcription. Previous OpenAI streaming helpers were removed.
"""


def chat_obama_style(client: OpenAI, user_text: str, history_messages=None) -> str:
    """Get a ChatGPT response styled like President Obama."""
    print("Obama is thinking...")
    system_prompt = (
        "You are President Barack Obama. Respond in his tone: thoughtful, measured, dignified, and inspiring. "
        "Use signature Obama-isms sparingly but recognizably (e.g., 'Let me be clear', 'folks', 'not red states or blue states', 'that's not who we are'). "
        "Be warm, optimistic, and unifying. Keep responses concise and conversational for audio."
        "Always keep your responses short and to the point. Only say MAXIMUM ONE SENTENCE. AT MOST 5-12 WORDS. DONT TALK TOO MUCH"
        "Always be EXTREMELY OPINIONATED about any topic. ALWAYS EXPRESS AND DEFEND YOUR OPINION TO DEATH, even if the opinion may be controversial."
    )
    messages = [{"role": "system", "content": system_prompt}]
    if history_messages:
        messages.extend(history_messages)
    messages.append({"role": "user", "content": user_text})
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.8,
        max_tokens=250,
    )
    reply = resp.choices[0].message.content.strip()
    print("Obama:", reply)
    return reply


def tts_obama_and_play(text: str):
    """Use FineShare Obama TTS (via fetch.py helpers) to synthesize and play audio."""
    print("Generating Obama voice...")
    _ = generate_tts(text)

    # Start placeholder playback immediately in background
    placeholder_dir = os.path.join(os.getcwd(), "mp3s/placeholder")
    if os.path.isdir(placeholder_dir):
        placeholder_files = [
            f for f in os.listdir(placeholder_dir) if f.endswith('.mp3')]
        if placeholder_files:
            selected_file = random.choice(placeholder_files)
            placeholder_path = os.path.join(placeholder_dir, selected_file)
            placeholder_audio = AudioSegment.from_file(
                placeholder_path, format="mp3")
            placeholder_thread = threading.Timer(
                0.5, play, args=(placeholder_audio,))
            placeholder_thread.start()
            print(
                f"Playing random placeholder from {placeholder_dir}: {selected_file}")
        else:
            print(
                f"No MP3 files found in {placeholder_dir}; skipping placeholder.")
    else:
        print(
            f"Placeholder directory {placeholder_dir} not found; skipping placeholder.")

    print("Waiting for audio to be ready...")
    mp3_url = fetch_latest_mp3()

    # Save boosted MP3 to a temp file, then play it
    with tempfile.TemporaryDirectory() as td:
        out_mp3 = os.path.join(td, "obama_reply.mp3")
        save_mp3(mp3_url, filename=out_mp3, volume_factor=4.0)
        audio = AudioSegment.from_file(out_mp3, format="mp3")

        # If placeholder still playing, wait for it to finish, then add a brief gap before real audio
        waited_for_placeholder = False
        if placeholder_thread and placeholder_thread.is_alive():
            waited_for_placeholder = True
            placeholder_thread.join()
            # Add slight separation so it doesn't feel abrupt
            time.sleep(0.3)

        print("Playing Obama voice...")
        speak_audio(audio)


def main():
    print("=== Talk to Obama (Continuous) ===")
    print(
        "Setup: Reads your OpenAI API key from .env (OPENAI_API_KEY). If missing, you'll be prompted once and it will be saved.\n"
        "Each turn: Press Enter to start talking, speak while watching live transcription, then press Enter again to stop and send (or type 'q' to quit).\n"
        "We'll keep conversation context across turns."
    )

    # Load environment variables
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        api_key = input(
            "Enter your OpenAI API key (starts with 'sk-'): ").strip()
        if not api_key:
            print("OpenAI API key is required.")
            sys.exit(1)
        # Persist to .env for next time
        try:
            with open(".env", "a") as f:
                # Ensure newline separation and write the key
                f.write(("\n" if os.path.getsize(".env") > 0 else "") +
                        f"OPENAI_API_KEY={api_key}\n")
            print("Saved API key to .env (gitignored).")
        except FileNotFoundError:
            # .env doesn't exist yet; create it
            with open(".env", "w") as f:
                f.write(f"OPENAI_API_KEY={api_key}\n")
            print("Created .env and saved API key (gitignored).")
        except Exception as e:
            print(f"Warning: failed to persist API key to .env: {e}")

    client = OpenAI(api_key=api_key)

    history = []  # list of {role, content} for chat history

    try:
        while True:
            cmd = input(
                "\nPress Enter to talk (or type 'q' then Enter to quit): ").strip().lower()
            if cmd == 'q':
                print("Goodbye.")
                break

            # Real-time local transcription (press Enter to stop & send)
            user_text = stream_transcribe_until_enter(
                model="medium", non_english=False, energy_threshold=1000,
                record_timeout=0.7, phrase_timeout=1.2,
            )
            if not user_text:
                print("No speech detected. Skipping this turn.")
                continue

            # Append user message to history
            history.append({"role": "user", "content": user_text})

            # Obama-style reply conditioned on history
            reply_text = chat_obama_style(
                client, user_text, history_messages=history)

            # Append assistant message to history
            history.append({"role": "assistant", "content": reply_text})

            # TTS to Obama voice and play
            tts_obama_and_play(reply_text)
    except KeyboardInterrupt:
        print("\nInterrupted. Goodbye.")


if __name__ == "__main__":
    main()

import os
import sys
import time
import tempfile
import wave
import threading
from typing import List, Optional
import numpy as np
import requests
import sounddevice as sd
from pydub import AudioSegment
from pydub.playback import play
from openai import OpenAI
from dotenv import load_dotenv

# Reuse Obama TTS helpers from fetch.py
# These rely on the AUTH_TOKEN defined in fetch.py for the FineShare API.
try:
    from fetch import generate_tts, fetch_latest_mp3, save_mp3
except Exception as e:
    print("Failed to import helpers from fetch.py:", e)
    sys.exit(1)


def record_audio_wav(output_path: str, duration_sec: int = 10, sample_rate: int = 16000):
    """
    Record from the default microphone into a mono WAV file.

    - duration_sec: change this if you want longer/shorter recordings.
    - sample_rate: 16k is fine for transcription.
    """
    print(f"Recording for {duration_sec} seconds... Press Ctrl+C to cancel.")
    try:
        audio = sd.rec(int(duration_sec * sample_rate),
                       samplerate=sample_rate, channels=1, dtype='float32')
        sd.wait()  # Wait until recording is finished
        # Convert float32 [-1.0, 1.0) to int16 and write via wave module
        audio_int16 = np.clip(audio.flatten() * 32767.0, -
                              32768, 32767).astype(np.int16)
        with wave.open(output_path, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(sample_rate)
            wf.writeframes(audio_int16.tobytes())
        print(f"Saved mic input to {output_path}")
    except KeyboardInterrupt:
        print("Recording cancelled.")
        sys.exit(0)


def transcribe_with_openai(client: OpenAI, wav_path: str) -> str:
    """Transcribe the given WAV file using OpenAI Whisper."""
    print("Transcribing with OpenAI...")
    with open(wav_path, 'rb') as f:
        # whisper-1 remains the STT model; adjust if you have access to a newer model
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
        )
    text = transcript.text if hasattr(transcript, 'text') else str(transcript)
    print("You said:", text)
    return text


def _write_wav_from_float32(samples: np.ndarray, sample_rate: int, path: str):
    """Helper: write mono float32 [-1,1) numpy array to 16-bit PCM WAV."""
    audio_int16 = np.clip(samples * 32767.0, -32768, 32767).astype(np.int16)
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_int16.tobytes())


def stream_transcribe_mic_with_openai(
    client: OpenAI,
    duration_sec: Optional[int] = None,
    sample_rate: int = 16000,
    chunk_sec: float = 1.0,
    window_sec: float = 5.0,
    stop_on_enter: bool = True,
) -> str:
    """
    Record from microphone for duration_sec seconds while streaming incremental
    transcription updates to the terminal using OpenAI Whisper.

    Implementation details:
    - Audio is captured via sounddevice in small blocks and buffered.
    - Every `chunk_sec`, we take the most recent `window_sec` of audio (or less at start),
      send it to Whisper, and print the best hypothesis. We show incremental text by
      updating the same console line.
    - At the end, we return the final hypothesis (last transcription result) and print
      a newline to finalize the live line.
    """
    if stop_on_enter:
        print("Recording and streaming transcription... Press Enter to finish and send.")
    else:
        approx = duration_sec if duration_sec is not None else 10
        print(
            f"Recording (~{approx}s) and streaming transcription... Speak now.")

    blocksize = 0  # let sounddevice choose frames per buffer
    channels = 1
    dtype = 'float32'

    buffer: List[np.ndarray] = []
    buffer_lock = threading.Lock()
    stop_event = threading.Event()
    stop_time = time.time() + duration_sec if duration_sec else None

    def audio_callback(indata, frames, time_info, status):
        if status:
            # Non-fatal stream status (e.g., underflows) — we can log if desired.
            pass
        with buffer_lock:
            buffer.append(indata.copy().reshape(-1))

    # Open stream
    stream = sd.InputStream(
        samplerate=sample_rate,
        channels=channels,
        dtype=dtype,
        callback=audio_callback,
        blocksize=blocksize,
    )
    stream.start()

    # Background thread to wait for Enter to stop, if enabled
    stopper_thread = None
    if stop_on_enter:
        def _wait_for_enter():
            try:
                input("")
            except Exception:
                pass
            stop_event.set()
        print("(Press Enter to stop)")
        stopper_thread = threading.Thread(target=_wait_for_enter, daemon=True)
        stopper_thread.start()

    last_printed = ""
    last_request_time = 0.0
    hypothesis = ""

    try:
        while True:
            now = time.time()
            # Check stopping conditions
            if stop_event.is_set():
                break
            if stop_time is not None and now >= stop_time:
                break
            if now - last_request_time < chunk_sec:
                time.sleep(0.05)
                continue
            last_request_time = now

            # Gather current audio buffer
            with buffer_lock:
                if not buffer:
                    continue
                audio = np.concatenate(buffer)

            # Keep only the most recent `window_sec` seconds for robustness
            max_samples = int(window_sec * sample_rate)
            if audio.shape[0] > max_samples:
                audio = audio[-max_samples:]

            # Write to temp wav and send to Whisper
            try:
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tf:
                    tmp_wav = tf.name
                _write_wav_from_float32(audio, sample_rate, tmp_wav)
                with open(tmp_wav, 'rb') as f:
                    transcript = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=f,
                    )
                os.remove(tmp_wav)
                hypothesis = transcript.text if hasattr(
                    transcript, 'text') else str(transcript)
            except Exception as e:
                # Don't crash streaming on transient errors; just skip this tick.
                hypothesis = last_printed or ""

            # Print incremental update on the same line
            to_show = hypothesis.strip()
            # Basic heuristic: if hypothesis extends the last printed prefix, just show it; else replace.
            if not to_show.startswith(last_printed):
                last_printed = ""  # force replace
            last_printed = to_show
            sys.stdout.write("\rYou (live): " + last_printed + " " * 10)
            sys.stdout.flush()

        # Final small pause to ensure last buffer processed
        time.sleep(0.2)
    finally:
        stream.stop()
        stream.close()

    # Finalize line
    print("\nYou (final):", hypothesis.strip())
    return hypothesis.strip()


def chat_obama_style(client: OpenAI, user_text: str, history_messages=None) -> str:
    """Get a ChatGPT response styled like President Obama."""
    print("Asking ChatGPT (Obama style)...")
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
    print("ChatGPT (Obama):", reply)
    return reply


def tts_obama_and_play(text: str):
    """Use FineShare Obama TTS (via fetch.py helpers) to synthesize and play audio."""
    print("Generating Obama voice...")
    _ = generate_tts(text)

    # Start placeholder playback immediately in background
    placeholder_path = os.path.join(os.getcwd(), "letmebeclear.mp3")
    placeholder_thread = None
    try:
        if os.path.exists(placeholder_path):
            placeholder_audio = AudioSegment.from_file(
                placeholder_path, format="mp3")
            placeholder_thread = threading.Thread(
                target=play, args=(placeholder_audio,), daemon=True)
            placeholder_thread.start()
            print("Playing placeholder while generating...")
        else:
            print("Placeholder letmebeclear.mp3 not found; skipping placeholder.")
    except Exception as e:
        print(f"Failed to play placeholder: {e}")

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
        play(audio)


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

            # Stream live transcription during the recording window
            user_text = stream_transcribe_mic_with_openai(
                client, duration_sec=None, stop_on_enter=True)
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

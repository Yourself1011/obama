#! python3.7

import argparse
import os
import numpy as np
import whisper
import torch
import sounddevice as sd

from datetime import datetime, timedelta
from queue import Queue
from time import sleep
from typing import Optional, List
import threading


def stream_transcribe_until_enter(
    model: str = "medium",
    non_english: bool = False,
    energy_threshold: int = 1000,  # Ignored in sounddevice path (kept for API compat)
    record_timeout: float = 0.5,   # seconds per chunk
    phrase_timeout: float = 1.2,   # seconds of silence to segment
    default_microphone: Optional[str] = None,  # Ignored; use OS default
    sample_rate: int = 16000,
    window_sec: float = 5.0,
) -> str:
    """Real-time mic transcription using Whisper + sounddevice; stops on Enter.

    Captures audio in short blocks, transcribes a rolling window for faster
    perceived latency. Returns the final transcribed text when Enter is pressed.
    """
    # Load whisper model
    use_model = model if (model == "large" or non_english) else model + ".en"
    audio_model = whisper.load_model(use_model)

    # Rolling audio buffer
    buffer: List[np.ndarray] = []
    buffer_lock = threading.Lock()
    stop_event = threading.Event()
    last_audio_time = None

    def audio_callback(indata, frames, time_info, status):
        nonlocal last_audio_time
        if status:
            # Non-fatal under/overflows; can log if desired
            pass
        with buffer_lock:
            buffer.append(indata.copy().reshape(-1))
        last_audio_time = datetime.utcnow()

    # Start input stream
    stream = sd.InputStream(
        samplerate=sample_rate,
        channels=1,
        dtype='float32',
        callback=audio_callback,
        blocksize=int(record_timeout * sample_rate),
    )
    stream.start()

    def _wait_for_enter():
        try:
            input("")
        except Exception:
            pass
        stop_event.set()

    print("(Press Enter to stop)")
    threading.Thread(target=_wait_for_enter, daemon=True).start()

    transcription = ['']
    last_text = ''

    print("Model loaded. Speak now...\n")

    try:
        while not stop_event.is_set():
            # Gather current audio buffer
            with buffer_lock:
                if not buffer:
                    pass
                else:
                    audio = np.concatenate(buffer)
                    # Limit to last window_sec seconds
                    max_samples = int(window_sec * sample_rate)
                    if audio.shape[0] > max_samples:
                        audio = audio[-max_samples:]

                    # Segmenting on silence: if too much time passed since last audio chunk
                    phrase_complete = False
                    if last_audio_time is not None and (datetime.utcnow() - last_audio_time) > timedelta(seconds=phrase_timeout):
                        phrase_complete = True

            if buffer:
                # Transcribe current rolling window
                try:
                    result = audio_model.transcribe(audio, fp16=torch.cuda.is_available())
                    text = result.get('text', '').strip()
                except Exception:
                    text = last_text
                if text:
                    last_text = text
                    if phrase_complete:
                        transcription.append(text)
                    else:
                        transcription[-1] = text

                # Live update
                os.system('cls' if os.name == 'nt' else 'clear')
                for line in transcription:
                    print(line)
                print('', end='', flush=True)

            sleep(0.1)
    finally:
        stream.stop()
        stream.close()

    sleep(0.2)
    return last_text.strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="medium", choices=["tiny", "base", "small", "medium", "large"], help="Whisper model")
    parser.add_argument("--non_english", action='store_true', help="Use multi-lingual model (not .en)")
    parser.add_argument("--record_timeout", default=0.5, type=float, help="Block duration in seconds")
    parser.add_argument("--phrase_timeout", default=1.2, type=float, help="Silence gap to segment in seconds")
    args = parser.parse_args()

    # Run the streaming transcriber and print the final text
    text = stream_transcribe_until_enter(
        model=args.model,
        non_english=args.non_english,
        record_timeout=args.record_timeout,
        phrase_timeout=args.phrase_timeout,
    )
    print("\n\nFinal:")
    print(text)


if __name__ == "__main__":
    main()

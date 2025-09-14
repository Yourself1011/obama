"""FineShare Obama TTS helpers.

Reads FINESHARE_API_TOKEN from environment (or .env via caller) to authorize.
"""

import requests
import time
import os
import math
from io import BytesIO
from pydub import AudioSegment


def _headers():
    token = os.getenv("FINESHARE_API_TOKEN", "").strip()
    if not token:
        token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VySWQiOiI4ZWYwZWYwOS1iZmMwLTQ5MDAtOGE0Yy1lNjhmMTk3MjYwZTgiLCJ1c2VyQWNjb3VudCI6Imo4emFuZ3V3QGdtYWlsLmNvbSJ9.ZX2j5blwP3fqkGv2KG-JHB3WunHA5MaxKzDzgfltpLA"
        # raise RuntimeError(
        # "FINESHARE_API_TOKEN is not set. Add it to your .env or environment.")
    return {
        "client": "tts",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }


def generate_tts(text: str):
    url = "https://converter.fineshare.com/api/fsmstexttospeech"
    data = {
        "engine": "gpt-api",
        "appId": "107",
        "featureId": "22",
        "speech": f"<mstts:express-as style=\"normal\" styledegree=\"1\"><prosody rate=\"0.0%\" pitch=\"+0.00%\">{text}</prosody></mstts:express-as>",
        "voice": "obama-228616",
        "Speed": 1,
        "ChangerType": 3,
        "designUuid": None,
        "platform": "web-app-tts-obama-228616",
        "Parameter": {
            "speed": 1,
            "languageCode": "en-US",
            "outputSpeed": 1,
            "outputGender": 1,
            "name": "obama-228616",
            "ssml": True,
            "effect": None,
            "amotion": None,
            "pitch": 0
        }
    }

    resp = requests.post(url, headers=_headers(), json=data, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if data.get("available_count", 1) == 0:
        raise Exception("No available TTS")
    return data


def fetch_latest_mp3():
    url = "https://voiceai.fineshare.com/api/listmyvoicefiles?page=0&limit=1&status=4"
    while True:
        resp = requests.get(url, headers=_headers(), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        # Try multiple known response shapes
        file_url = None
        try:
            # Shape A: { "files": [ { "cover": { "url": "..." } } ] }
            files = data.get("files")
            if isinstance(files, list) and files:
                file_url = files[0].get("cover", {}).get("url")
        except Exception:
            pass
        if not file_url:
            try:
                # Shape B: { "data": { "list": [ { "fileUrl": "..." } ] } }
                file_url = data.get("data", {}).get(
                    "list", [{}])[0].get("fileUrl")
            except Exception:
                pass
        if file_url:
            return file_url
        print("Waiting for generation...")
        time.sleep(2)


def save_mp3(file_url, filename="output.mp3", volume_factor=4):
    """Download MP3, increase volume, and save.

    volume_factor: linear amplitude multiplier (1.5 = +50%).
    Requires ffmpeg installed and accessible for pydub.
    """
    resp = requests.get(file_url, timeout=60)
    resp.raise_for_status()

    # Load MP3 from memory, apply gain in dB, and export
    audio = AudioSegment.from_file(BytesIO(resp.content), format="mp3")
    gain_db = 20 * math.log10(volume_factor)
    louder = audio.apply_gain(gain_db)
    louder.export(filename, format="mp3")
    print(f"Saved MP3 as {filename} (+{gain_db:.2f} dB)")


if __name__ == "__main__":
    # index = 9
    # for phrase in ["my name is fork boy. i resemble a fork", "If you’re walking down the right path and you’re willing to keep walking, eventually you’ll make progress.", "Hope is not blind optimism.", "Change doesn’t come from Washington. Change comes to Washington.", "This is not about me. This is about us.", "We rise or fall as one nation, as one people.", "America is not a collection of red states and blue states, but the United States.", "The arc of history is long, but it bends toward justice.", "Our destiny is not written for us, but by us.", "We are one people.", "There’s not a liberal America and a conservative America — there’s the United States of America.", "I stand here knowing that my story is part of the larger American story.", "We can’t wait.", "That’s not who we are.", "The future rewards those who press on.", "I believe in the American Dream."]:
    #     print("Requesting TTS generation...")
    #     generate_tts(phrase)

    #     print("Fetching latest MP3 URL...")
    #     mp3_url = fetch_latest_mp3()
    #     save_mp3(mp3_url, f"obama_{index}.mp3")
    #     save_mp3(mp3_url, f"output.mp3")
    #     index += 1

    print("Requesting TTS generation...")
    generate_tts(
        "Hmmmmmmm? Oh. Yes.")

    print("Fetching latest MP3 URL...")
    mp3_url = fetch_latest_mp3()
    save_mp3(mp3_url, f"output.mp3")

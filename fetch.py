import requests
import time
import os

# Authorization token (keep safe!)
AUTH_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VySWQiOiJhMzZmMzE2Yy1jZDk3LTQxZDQtYmIwMS0wNTNhZTQ5OTJhMjUiLCJ1c2VyQWNjb3VudCI6ImxpZmVuZy55aW4uMDdAZ21haWwuY29tIn0.lq_Rh71fgNFDoRqS7mQ6ZyC0VD2hidMMN5ubUK2664o"

HEADERS = {
    "client": "tts",
    "Content-Type": "application/json",
    "Authorization": f"Bearer {AUTH_TOKEN}"
}


def generate_tts(text):
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

    resp = requests.post(url, headers=HEADERS, json=data)
    resp.raise_for_status()
    return resp.json()


def fetch_latest_mp3():
    url = "https://voiceai.fineshare.com/api/listmyvoicefiles?page=0&limit=1&status=4"
    while True:
        resp = requests.get(url, headers=HEADERS)
        resp.raise_for_status()
        data = resp.json()
        items = data.get("data", {}).get("items", [])
        if items:
            file_url = items[0].get("url")
            if file_url:
                return file_url
        print("Waiting for generation...")
        time.sleep(2)


def save_mp3(file_url, filename="output.mp3"):
    resp = requests.get(file_url, stream=True)
    resp.raise_for_status()
    with open(filename, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    print(f"Saved MP3 as {filename}")


if __name__ == "__main__":
    text = "SPOKEN TEXT GOES HERE"
    print("Requesting TTS generation...")
    generate_tts(text)

    print("Fetching latest MP3 URL...")
    mp3_url = fetch_latest_mp3()
    save_mp3(mp3_url)

import pexpect
import re
import os
from pydub import AudioSegment
from pydub.playback import play

# --- Config ---
SSH_HOST = "10.37.99.165"
SSH_USER = "jeffrey-zang"
SSH_PASS = "obama"
REMOTE_CMD = "source /home/jeffrey-zang/obama/venv/bin/activate && python /home/jeffrey-zang/obama/utils/speak.py"
LOCAL_AUDIO_DIR = "./mp3s"
PATTERN = re.compile(r"Playing:\s*(\S+)")

# --- Start SSH session ---
child = pexpect.spawn(f"ssh {SSH_USER}@{SSH_HOST} {REMOTE_CMD}")
child.expect("password:")
child.sendline(SSH_PASS)

# --- Stream output ---
while True:
    try:
        line = child.readline().decode().strip()
        if not line:
            continue
        print(line)

        match = PATTERN.search(line)
        if match:
            filename = match.group(1)
            filepath = os.path.join(LOCAL_AUDIO_DIR, filename)

            if os.path.exists(filepath):
                print(f"Playing local file: {filepath}")
                sound = AudioSegment.from_file(filepath)
                play(sound)  # actually plays locally
            else:
                print(f"File not found locally: {filepath}")

    except pexpect.EOF:
        print("SSH session ended.")
        break
    except KeyboardInterrupt:
        print("Exiting.")
        break


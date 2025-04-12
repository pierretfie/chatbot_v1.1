import subprocess
import shutil
import os
import shlex

# --- Configuration ---
MODEL_PATH = os.path.expanduser('~/piper_models/en_GB-jenny_dioco-medium/en_GB-jenny_dioco-medium.onnx')
TEXT_TO_SPEAK = "This sentence is spoken first. This sentence is synthesized while the first sentence is spoken."
SAMPLE_RATE = "22050"  # Adjust based on model specs
# --- End Configuration ---

# --- Check if piper is installed ---
PIPER_CMD = shutil.which("piper")  # Finds 'piper' in system $PATH
if not PIPER_CMD:
    print("❌ Error: 'piper' is not installed or not found in PATH.")
    print("🔍 Try running: 'which piper' or reinstall with: 'pip install piper-tts'")
    exit(1)

# --- Check if model exists ---
if not os.path.exists(MODEL_PATH):
    print(f"❌ Error: Piper model not found at: {MODEL_PATH}")
    print("🛠️ Make sure the model is downloaded and correctly placed.")
    exit(1)

# --- Check if 'aplay' is installed ---
if not shutil.which("aplay"):
    print("❌ Error: 'aplay' not found. Install it with: sudo apt install alsa-utils")
    exit(1)

# --- Piper and aplay commands ---
piper_cmd = [
    PIPER_CMD,
    "--model", MODEL_PATH,
    "--output-raw"
]

aplay_cmd = [
    "aplay",
    "-r", SAMPLE_RATE,
    "-f", "S16_LE",  # Signed 16-bit Little-Endian PCM
    "-t", "raw",
    "-"
]

print("\n🚀 --- Running Piper ---")
print(f"📜 Command: {' '.join(shlex.quote(arg) for arg in piper_cmd)}")
print(f"📢 Input Text: '{TEXT_TO_SPEAK}'")

try:
    # Start Piper process
    piper_process = subprocess.Popen(piper_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Start aplay process
    aplay_process = subprocess.Popen(aplay_cmd, stdin=piper_process.stdout, stderr=subprocess.PIPE)

    # Close stdout to prevent deadlocks
    piper_process.stdout.close()

    # Send text input to Piper
    _, piper_stderr = piper_process.communicate(input=TEXT_TO_SPEAK.encode("utf-8"))

    # Wait for aplay to finish
    aplay_stdout, aplay_stderr = aplay_process.communicate()

    print("\n✅ --- Finished ---")

    # --- Error Handling ---
    if piper_process.returncode != 0:
        print(f"❌ Piper exited with error code: {piper_process.returncode}")
        if piper_stderr:
            error_msg = piper_stderr.decode("utf-8", errors="ignore").strip()
            print(f"🛠️ Piper stderr: {error_msg}")
            if "No such file or directory" in error_msg:
                print("🔍 Possible issue: The model file might be missing or incorrect.")

    if aplay_process.returncode != 0:
        print(f"❌ aplay exited with error code: {aplay_process.returncode}")
        if aplay_stderr:
            error_msg = aplay_stderr.decode("utf-8", errors="ignore").strip()
            print(f"🔊 aplay stderr: {error_msg}")
            if "device busy" in error_msg.lower():
                print("🛠️ Possible fix: Try running 'sudo fuser -v /dev/snd/*' to find processes using audio.")

    if piper_process.returncode == 0 and aplay_process.returncode == 0:
        print("🎉 Speech playback completed successfully!")

except FileNotFoundError as e:
    print(f"❌ Error: Command not found - {e.filename}")
    print("📌 Ensure both Piper and 'aplay' are installed and accessible.")
except Exception as e:
    print(f"❌ An unexpected error occurred: {e}")

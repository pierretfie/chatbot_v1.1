import subprocess
import os
import shlex # Used for debugging print output

# --- Configuration ---
# !! ADJUST THESE PATHS !!
piper_dir = os.path.expanduser('~/piper_models/piper') # Directory containing the piper executable
model_path = os.path.expanduser('~/piper_models/en_GB-jenny_dioco-medium/en_GB-jenny_dioco-medium.onnx')

# Construct the full path to the piper executable
piper_executable = os.path.join(piper_dir, 'piper')

text_to_speak = ('Dark matter is one of the most intriguing and mysterious concepts in modern cosmology.\n'
'It refers to a form of matter that does not emit, absorb, or reflect light, making it invisible to telescopes and other traditional detection methods.\n'
'Despite this, dark matter constitutes approximately 27% of the total mass-energy content of the universe, while ordinary (baryonic) matter makes up\n'
'only about 5%. The remaining 68% is attributed to dark energy, which is responsible for the accelerated expansion of the universe.')
sample_rate = '22050' # Sample rate for the specific model
# --- End Configuration ---

# --- Verify files exist ---
if not os.path.exists(piper_executable):
    print(f"Error: Piper executable not found at: {piper_executable}")
    exit(1)
if not os.path.exists(model_path):
    print(f"Error: Piper model not found at: {model_path}")
    exit(1)
# Check if aplay exists (optional, but good practice)
try:
    subprocess.run(['aplay', '--version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
except (subprocess.CalledProcessError, FileNotFoundError):
    print(f"Error: 'aplay' command not found or not working. Please ensure it's installed (e.g., 'sudo apt install alsa-utils' on Debian/Ubuntu).")
    exit(1)
# --- End Verification ---


# Construct the command arguments as lists
piper_cmd = [
    piper_executable,
    '--model', model_path,
    '--output-raw'
]

aplay_cmd = [
    'aplay',
    '-r', sample_rate,
    '-f', 'S16_LE', # Signed 16-bit Little-Endian PCM
    '-t', 'raw',    # Input type is raw audio data
    '-'             # Read from standard input
]

print("--- Running Piper ---")
print(f"Command: {' '.join(shlex.quote(arg) for arg in piper_cmd)}")
print(f"Input Text: '{text_to_speak}'")
print("\n--- Piping to aplay ---")
print(f"Command: {' '.join(shlex.quote(arg) for arg in aplay_cmd)}")
print("\nSpeaking...")

try:
    # Start the piper process
    # - stdin=subprocess.PIPE: Allows us to send text to it
    # - stdout=subprocess.PIPE: Captures its raw audio output
    # - stderr=subprocess.PIPE: Captures any error messages
    piper_process = subprocess.Popen(piper_cmd,
                                     stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)

    # Start the aplay process
    # - stdin=piper_process.stdout: Connects aplay's input directly to piper's output
    # - stderr=subprocess.PIPE: Captures any error messages from aplay
    aplay_process = subprocess.Popen(aplay_cmd,
                                     stdin=piper_process.stdout,
                                     stderr=subprocess.PIPE)

    # Allow piper_process.stdout to be closed properly when aplay is done reading.
    # This helps prevent potential deadlocks if aplay finishes before piper.
    piper_process.stdout.close() # SIGPIPE handling

    # Send the text to piper's stdin and close its stdin
    # We use communicate() which handles writing input, closing stdin,
    # and waiting for the process to finish. We only care about stderr here.
    _, piper_stderr = piper_process.communicate(input=text_to_speak.encode('utf-8'))

    # Wait for aplay to finish and capture its stderr
    aplay_stdout, aplay_stderr = aplay_process.communicate()

    # --- Check for errors ---
    print("\n--- Finished ---")
    if piper_process.returncode != 0:
        print(f"Piper process exited with error code: {piper_process.returncode}")
        if piper_stderr:
            print("Piper stderr:")
            print(piper_stderr.decode('utf-8', errors='ignore').strip())

    if aplay_process.returncode != 0:
        print(f"aplay process exited with error code: {aplay_process.returncode}")
        if aplay_stderr:
            print("aplay stderr:")
            print(aplay_stderr.decode('utf-8', errors='ignore').strip())

    if piper_process.returncode == 0 and aplay_process.returncode == 0:
        print("Playback completed successfully.")

except FileNotFoundError as e:
    print(f"\nError: Command not found - {e.filename}")
    print("Please ensure both the piper executable path and 'aplay' are correct and accessible.")
except Exception as e:
    print(f"\nAn unexpected error occurred: {e}")
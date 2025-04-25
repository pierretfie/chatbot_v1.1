import requests
import subprocess
import tempfile
import os
import gc
import json

def tts_from_server(text, port=5002, speaker_id="", style_wav="", language_id=""):
    # Use query parameters as seen in the server's JavaScript code
    url = f"http://localhost:{port}/api/tts"
    
    # Add query parameters
    params = {
        "text": text,
        "speaker_id": speaker_id,
        "style_wav": style_wav,
        "language_id": language_id
    }
    
    print(f"[DEBUG] Sending request with params:\n{json.dumps(params, indent=2)}")
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
            response = requests.get(url, params=params, stream=True)

            if response.status_code != 200:
                print(f"[✗] Error {response.status_code}: {response.text}")
                return

            for chunk in response.iter_content(chunk_size=4096):
                if chunk:
                    f.write(chunk)

            temp_path = f.name

        print(f"[♪] Playing audio...")
        subprocess.call(["aplay", temp_path])
        os.remove(temp_path)
        gc.collect()

    except Exception as e:
        print(f"[!] Exception during request: {e}")

# Main interactive loop
def main():
    print("🎙️  Coqui TTS Client - Type your message below")
    print("💡 Type 'exit' or 'quit' to stop.\n")

    while True:
        try:
            user_input = input("📝 Text to speak: ").strip()
            if user_input.lower() in {"exit", "quit"}:
                print("👋 Goodbye!")
                break
            elif len(user_input) == 0:
                continue
            else:
                tts_from_server(user_input)
        except Exception as e:
            print(f"[!] Input error: {e}")

if __name__ == "__main__":
    main()

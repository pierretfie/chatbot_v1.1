from gradio_client import Client, handle_file
import os
import sys

def init():
    global client
    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        raise RuntimeError("Please set your Hugging Face token in the HF_TOKEN environment variable.")
    client = Client("jimmyvu/Coqui-Xtts-Demo", hf_token=hf_token)

def generate_audio(text):
    # Prepend a neutral pause to avoid losing initial words
    safe_text = f". {text}"
    result = client.predict(
        input_text=safe_text,
        speaker_reference_audio=handle_file("/home/eclipse/Desktop/gideon_voice_piper/my_gideon_dataset/wavs/gideon_0001.wav"),
        enhance_speech=False,
        temperature=0.3,
        top_p=0.85,
        top_k=50,
        repetition_penalty=9.5,
        language="Auto",
        api_name="/generate_speech"
    )
    if result and result[0]:
        audio_path = result[0]
        return audio_path
    else:
        print("No audio file returned.")
        return None

def play_audio_file(audio_path):
    #print(f"Playing audio: {audio_path}")
    # Try to play audio using aplay, paplay, or ffplay
    played = False
    for player in ["paplay", "aplay", "ffplay -autoexit -nodisp"]:
        cmd = f"{player} '{audio_path}'"
        exit_code = os.system(cmd)
        if exit_code == 0:
            played = True
            break
    if not played:
        print(f"Could not play audio. Please play it manually: {audio_path}")
    else:
        pass
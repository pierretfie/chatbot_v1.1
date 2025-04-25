import numpy as np
import subprocess
from TTS.api import TTS
import os
import tempfile
import wave
import gc

# Initialize the TTS model (lightweight, fast on CPU)
tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC", progress_bar=False, gpu=False)

# Safe conversion of waveform to 16-bit PCM
def safe_wav_to_pcm(wav):
    if isinstance(wav, list):
        wav = np.array(wav)
    elif wav is None:
        raise ValueError("TTS returned None. Model may have failed to synthesize.")
    
    wav = wav * 32767
    wav = np.clip(wav, -32768, 32767)
    return wav.astype(np.int16)

# Synthesize, normalize, save and play
def synthesize_and_play(text):
    print(f"[▶] Synthesizing: '{text[:50]}...'")  # Print just a preview of the text
    
    # TTS synthesis
    wav = tts.tts(text=text)
    print(f"[✓] TTS synthesis done. Waveform length: {len(wav)}")

    # Convert to PCM safely
    wav_int16 = safe_wav_to_pcm(wav)

    # Write to temp WAV file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
        with wave.open(f.name, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 2 bytes = 16 bits
            wf.setframerate(22050)  # Using default model sample rate
            wf.writeframes(wav_int16.tobytes())

        print(f"[♪] Playing audio using 'aplay': {f.name}")
        subprocess.call(["aplay", f.name])

    # Clean up
    os.remove(f.name)
    gc.collect()  # Free memory

# Run test
if __name__ == "__main__":
    text = '''Kasongo and the Whispering Baobab

In the heart of a village nestled between rolling hills and golden savannas, lived a young man named Kasongo. His name meant “the traveler,” though he had never stepped beyond the edge of his village. Still, there was something in his eyes that always seemed to be looking far away.

Kasongo wasn’t like the other boys. While they raced by the river and hunted birds with slingshots, he listened to stories told by the elders, his head tilted, eyes wide, heart hungry. He would sketch maps in the dust with a stick—maps of places he’d only heard of in hushed tales and fire-lit songs.

One evening, the village’s ancient baobab began to whisper.

'''

    synthesize_and_play(text)

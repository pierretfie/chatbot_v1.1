import numpy as np
import subprocess
from TTS.api import TTS
import os
import tempfile
import wave
import gc
from rich.console import Console
import sys
import contextlib
import warnings
console = Console()

@contextlib.contextmanager
def suppress_output():
    """Context manager to suppress both stdout and stderr output"""
    with open(os.devnull, 'w') as devnull:
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = devnull
        sys.stderr = devnull
        try:
            yield
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

# Initialize the TTS model (lightweight, fast on CPU)
try:
    console.print(f'[dim][blue]Initializing TTS model...[/blue][/dim]')
    with suppress_output():
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC", progress_bar=False, gpu=False)
except Exception as e:
    console.print(f'[red]Error initializing TTS model: {e}[/red]')
    sys.exit(1)

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
    """Synthesize text to speech and play it using the same parameters as audiotest.py"""
    # TTS synthesis
    wav = tts.tts(text=text)

    # Convert to PCM safely
    wav_int16 = safe_wav_to_pcm(wav)

    # Write to temp WAV file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
        with wave.open(f.name, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 2 bytes = 16 bits
            wf.setframerate(22050)  # Using default model sample rate
            wf.writeframes(wav_int16.tobytes())

        # Play the audio
        subprocess.call(["aplay", f.name])

    # Clean up
    os.remove(f.name)
    gc.collect()  # Free memory
if __name__ == "__main__":
    synthesize_and_play("hello")
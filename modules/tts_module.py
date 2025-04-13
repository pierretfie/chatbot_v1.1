import os
# Set environment variables before any imports - improved NNPACK suppression
os.environ['NNPACK_WARNINGS'] = '0'
os.environ['PYTORCH_WARNINGS'] = '0'
os.environ['TORCH_WARNINGS'] = '0'
os.environ['TORCH_CPP_LOG_LEVEL'] = 'ERROR'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TensorFlow warnings
os.environ['CUDA_VISIBLE_DEVICES'] = ''  # Disable CUDA to avoid GPU-related warnings

import numpy as np
import subprocess
import tempfile
import wave
import gc
import sys
import contextlib
import warnings
import logging
from rich.console import Console
import threading # Add threading import

# Configure warnings and logging before imports
warnings.filterwarnings('ignore')
logging.getLogger().setLevel(logging.ERROR)
logging.getLogger('tensorflow').setLevel(logging.ERROR)
logging.getLogger('TTS').setLevel(logging.ERROR)

# Create a context manager for stderr redirection
@contextlib.contextmanager
def redirect_stderr():
    """Temporarily redirect stderr to /dev/null"""
    stderr_fd = sys.stderr.fileno()
    with open(os.devnull, 'w') as devnull:
        # Save a copy of the original stderr
        stderr_copy = os.dup(stderr_fd)
        # Replace stderr with /dev/null
        os.dup2(devnull.fileno(), stderr_fd)
        try:
            yield
        finally:
            # Restore the original stderr
            os.dup2(stderr_copy, stderr_fd)
            os.close(stderr_copy)

# Import TTS with all warnings suppressed
with redirect_stderr():
    from TTS.api import TTS
    from TTS.utils.manage import ModelManager
    # Monkey patch the ModelManager to suppress warnings
    ModelManager._set_default_manager = lambda *args, **kwargs: None

console = Console()

@contextlib.contextmanager
def suppress_output():
    """Context manager to suppress all output and warnings"""
    with open(os.devnull, 'w') as devnull:
        # Save original file descriptors
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        
        # Redirect stdout and stderr
        sys.stdout = devnull
        sys.stderr = devnull
        
        # Suppress logging
        logging.disable(logging.CRITICAL)
        
        # Suppress all warnings
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            try:
                yield
            finally:
                # Restore original file descriptors
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                # Restore logging
                logging.disable(logging.NOTSET)

# Initialize the TTS model (lightweight, fast on CPU)
try:
    console.print(f'[dim][blue]Initializing TTS model...[/blue][/dim]')
    with suppress_output(), redirect_stderr():
        tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC", progress_bar=False, gpu=False)
except Exception as e:
    console.print(f'[red]Error initializing TTS model: {e}[/red]')
    sys.exit(1)

def safe_wav_to_pcm(wav):
    """Safe conversion of waveform to 16-bit PCM"""
    if isinstance(wav, list):
        wav = np.array(wav)
    elif wav is None:
        raise ValueError("TTS returned None. Model may have failed to synthesize.")
    
    wav = wav * 32767
    wav = np.clip(wav, -32768, 32767)
    return wav.astype(np.int16)

# Renamed and modified: Now synthesizes and returns the temp file path
def synthesize_to_temp_file(text):
    """Synthesize text to speech and save to a temporary WAV file."""
    # TTS synthesis with suppressed output
    with suppress_output(), redirect_stderr():
        wav = tts.tts(text=text)

    # Convert to PCM safely
    wav_int16 = safe_wav_to_pcm(wav)

    # Write to temp WAV file
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
            temp_filename = f.name
            with wave.open(temp_filename, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 2 bytes = 16 bits
                wf.setframerate(22050)  # Using default model sample rate
                wf.writeframes(wav_int16.tobytes())
        return temp_filename
    except Exception as e:
        console.print(f"[red]Error writing temporary audio file: {e}[/red]")
        return None
    finally:
        gc.collect() # Still good to collect garbage after synthesis

# New function to play and then delete the audio file
def play_audio_file(file_path):
    """Plays the audio file using aplay and then deletes it."""
    if file_path and os.path.exists(file_path):
        try:
            # Play the audio with suppressed output
            subprocess.run(["aplay", file_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except subprocess.CalledProcessError as e:
            console.print(f"[yellow]Warning: aplay command failed: {e}. Is 'aplay' installed and working?[/yellow]")
        except FileNotFoundError:
            console.print(f"[yellow]Warning: 'aplay' command not found. Cannot play audio.[yellow]")
        except Exception as e:
            console.print(f"[red]Error playing audio file {file_path}: {e}[/red]")
        finally:
            # Clean up the temporary file
            try:
                os.remove(file_path)
            except OSError as e:
                console.print(f"[yellow]Warning: Could not delete temp file {file_path}: {e}[/yellow]")
            gc.collect() # Collect garbage after playback potentially frees up resources

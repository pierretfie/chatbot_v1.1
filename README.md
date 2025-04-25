# TinyLlama Voice Chatbot

A voice-enabled chatbot using TinyLlama and neural text-to-speech (TTS).

## Features

- Voice interaction using neural TTS (default: [TTS library](https://github.com/coqui-ai/TTS), Tacotron2-DDC model)
- Optional: Integrate with free/freemium API-based TTS (see below)
- GPU-accelerated inference with TinyLlama
- Resource management for optimal performance
- Modular architecture for easy maintenance
- Personalized, time-aware greetings ("Good morning, Peter, it has been 1 minute since we spoke...")
- Remembers user info across sessions (name, preferences, etc.)

## Requirements

- Python 3.8+
- CUDA-capable GPU (recommended)
- [TTS library](https://github.com/coqui-ai/TTS) (Tacotron2-DDC model, default)
- TinyLlama model (1.1B parameters)
- Required Python packages (see requirements.txt)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd tinyllama-voice-chatbot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up neural TTS:
- By default, uses [TTS library](https://github.com/coqui-ai/TTS) with Tacotron2-DDC model (downloaded automatically on first run).
- For better quality or cloud-based TTS, see **API Integration** below.

4. Download TinyLlama model:
- Place the model at `~/tinyllama/tinyllama-1.1b-chat-v1.0.Q5_K_M.gguf`

## Usage

Run the chatbot:
```bash
python main.py
```

## API-based TTS Integration (Optional)

You can use high-quality, free/freemium API-based TTS providers instead of the default local TTS:
- **OpenAI TTS** (API key, generous free tier)
- **Google Cloud TTS** (API key, free tier)
- **Microsoft Azure TTS** (API key, free tier)
- **ElevenLabs** (API key, limited free tier)
- **Coqui TTS via HuggingFace API** (free tier)

To use a cloud TTS provider, update `tts_module.py` and set your API key as needed.

## Project Structure

```
tinyllama-voice-chatbot/
├── main.py                 # Main chatbot script
├── modules/
│   ├── brain.py           # Reasoning module
│   ├── resource_manager.py # Resource management
│   ├── gpu_manager.py     # GPU management
│   ├── prompt_template.py # Prompt templates
│   ├── tts_module.py      # TTS abstraction (local & API)
│   └── ...
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Configuration

Adjust paths in `main.py`:
- `tts_dir`: Path to TTS executable (default: uses [TTS library](https://github.com/coqui-ai/TTS))
- `model_path`: Path to TTS model (default: uses Tacotron2-DDC model)
- `tinyllama_path`: Path to TinyLlama model

## License

MIT License 